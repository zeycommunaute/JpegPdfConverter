// Script for handling file input display and other UI interactions

document.addEventListener('DOMContentLoaded', function() {
    // Update file input label with selected filename
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.value.split('\\').pop();
            if (fileName) {
                // Display the file name in the button
                const submitBtn = this.nextElementSibling;
                if (submitBtn) {
                    submitBtn.classList.add('btn-success');
                }
            }
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            // Create and dispatch a click event on the close button
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                const clickEvent = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                closeBtn.dispatchEvent(clickEvent);
            }
        }, 5000);
    });

    // Add animation to process steps
    const processSteps = document.querySelectorAll('.process-step');
    processSteps.forEach((step, index) => {
        setTimeout(() => {
            step.style.opacity = '1';
            step.querySelector('.icon-circle').style.transform = 'scale(1.1)';
            setTimeout(() => {
                step.querySelector('.icon-circle').style.transform = 'scale(1)';
            }, 200);
        }, index * 300);
    });
});
