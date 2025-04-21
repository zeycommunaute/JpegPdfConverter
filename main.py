import os
import logging
from flask import Flask, render_template, request, redirect, url_for, send_file, session, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
import io
import uuid
import tempfile
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Temporary directory for file storage
TEMP_DIR = tempfile.gettempdir()

# Languages
LANGUAGES = {
    'fr': {
        'title': 'Convertisseur JPEG → PDF avec Pub',
        'upload_btn': 'Télécharger une image JPEG',
        'convert_btn': 'Convertir en PDF',
        'placeholder': 'Aucune image sélectionnée',
        'success': 'Image convertie avec succès!',
        'download_btn': 'Télécharger le PDF',
        'banner_text': 'Bannière publicitaire',
        'error': 'Erreur: Seuls les fichiers JPEG sont acceptés.',
        'processing_error': 'Erreur lors du traitement de l\'image.',
        'ad_space': 'Espace Publicitaire',
        'lang_switch': 'EN 🇬🇧'
    },
    'en': {
        'title': 'JPEG to PDF Converter with Ads',
        'upload_btn': 'Upload a JPEG image',
        'convert_btn': 'Convert to PDF',
        'placeholder': 'No image selected',
        'success': 'Image successfully converted!',
        'download_btn': 'Download PDF',
        'banner_text': 'Advertising Banner',
        'error': 'Error: Only JPEG files are accepted.',
        'processing_error': 'Error processing the image.',
        'ad_space': 'Advertisement Space',
        'lang_switch': 'FR 🇫🇷'
    }
}

def get_language():
    lang = request.args.get('lang')
    if lang in LANGUAGES:
        session['lang'] = lang
    return session.get('lang', 'fr')

def add_yellow_banner(image_data):
    try:
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        new_image = Image.new('RGB', (width, height + 50), color=(255, 255, 255))
        new_image.paste(image, (0, 0))

        draw = ImageDraw.Draw(new_image)
        draw.rectangle([0, height, width, height + 50], fill=(255, 255, 0))
        
        try:
            font = ImageFont.load_default()
            lang = get_language()
            text = LANGUAGES[lang]['banner_text']
            text_width = draw.textlength(text, font=font)
            text_position = ((width - text_width) // 2, height + 15)
            draw.text(text_position, text, fill=(0, 0, 0), font=font)
        except Exception as e:
            logging.error(f"Erreur ajout texte : {e}")

        buffer = io.BytesIO()
        new_image.save(buffer, format='JPEG')
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        logging.error(f"Erreur bannière : {e}")
        return None

def create_pdf(image_data):
    try:
        temp_image_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(image_data)

        with Image.open(temp_image_path) as img:
            width, height = img.size

        pdf = FPDF(unit="pt", format=[width, height])
        pdf.add_page()
        pdf.image(temp_image_path, 0, 0, width, height)

        temp_pdf_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.pdf")
        pdf.output(temp_pdf_path)
        os.remove(temp_image_path)

        return temp_pdf_path
    except Exception as e:
        logging.error(f"Erreur création PDF : {e}")
        if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        return None

@app.route('/', methods=['GET'])
def index():
    lang = get_language()
    texts = LANGUAGES[lang]
    return render_template('index.html', texts=texts, pdf_path=None, error=None)

@app.route('/convert', methods=['POST'])
def convert():
    lang = get_language()
    texts = LANGUAGES[lang]

    if 'file' not in request.files:
        return render_template('index.html', texts=texts, pdf_path=None, error="No file part")

    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', texts=texts, pdf_path=None, error="No file selected")

    if not file.filename.lower().endswith(('.jpg', '.jpeg')):
        return render_template('index.html', texts=texts, pdf_path=None, error=texts['error'])

    try:
        image_data = file.read()
        modified_image_data = add_yellow_banner(image_data)
        if not modified_image_data:
            return render_template('index.html', texts=texts, pdf_path=None, error=texts['processing_error'])

        pdf_path = create_pdf(modified_image_data)
        if not pdf_path:
            return render_template('index.html', texts=texts, pdf_path=None, error=texts['processing_error'])

        session['pdf_path'] = pdf_path
        session['pdf_filename'] = secure_filename(os.path.splitext(file.filename)[0] + '.pdf')

        return render_template('index.html', texts=texts, pdf_path=pdf_path, error=None)

    except Exception as e:
        logging.error(f"Erreur traitement : {e}")
        return render_template('index.html', texts=texts, pdf_path=None, error=texts['processing_error'])

@app.route('/download')
def download():
    pdf_path = session.get('pdf_path')
    if not pdf_path or not os.path.exists(pdf_path):
        return redirect(url_for('index'))

    filename = session.get('pdf_filename', 'converted.pdf')
    response = send_file(pdf_path, as_attachment=True, download_name=filename)

    @response.call_on_close
    def cleanup():
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as e:
            logging.error(f"Erreur suppression fichier : {e}")

    return response

@app.route('/switch-language')
def switch_language():
    lang = get_language()
    new_lang = 'en' if lang == 'fr' else 'fr'
    return redirect(url_for('index', lang=new_lang))

# 🔥 Route pour servir le fichier sw.js (Monetag)
@app.route('/sw.js')
def sw():
    return send_from_directory('.', 'sw.js')

@app.after_request
def after_request_func(response):
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
