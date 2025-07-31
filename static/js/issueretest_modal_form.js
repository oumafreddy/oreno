/**
 * Issue Retest Modal Form JavaScript
 * Handles issue retest-specific form logic
 * Generic form submission is now handled by modal-handler.js
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('issueretestForm');
    if (!form) return;

    // Handle form submission manually
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        submitBtn.disabled = true;

        // Get form data
        const formData = new FormData(form);
        
        // Send AJAX request
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'HX-Request': 'true'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.form_is_valid || data.success) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('globalModal'));
                if (modal) {
                    modal.hide();
                }
                
                // Update the list if provided
                if (data.html_list) {
                    const container = document.getElementById('issueretest-list-container');
                    if (container) {
                        container.innerHTML = data.html_list;
                    }
                }
                
                // Show success message
                if (window.ModalHandler && window.ModalHandler.showNotification) {
                    window.ModalHandler.showNotification(data.message || 'Retest saved successfully!', 'success');
                } else {
                    alert(data.message || 'Retest saved successfully!');
                }
                
                console.log('Retest saved successfully');
            } else if (data.html_form) {
                // Replace modal content with form containing errors
                const modalBody = document.querySelector('#globalModal .modal-body');
                if (modalBody) {
                    modalBody.innerHTML = data.html_form;
                }
            }
        })
        .catch(error => {
            console.error('Error saving retest:', error);
            if (window.ModalHandler && window.ModalHandler.showNotification) {
                window.ModalHandler.showNotification('An error occurred while saving the retest.', 'error');
            } else {
                alert('An error occurred while saving the retest.');
            }
        })
        .finally(() => {
            // Restore button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });

    // Add form validation
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });
}); 