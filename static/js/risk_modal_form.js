/**
 * Risk Modal Form JavaScript
 * Handles risk-specific form logic
 * Generic modal functionality is now handled by modal-handler.js
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('riskForm');
    if (!form) return;

    // Use ModalHandler for enhanced form submission handling
    if (window.ModalHandler) {
        window.ModalHandler.handleFormSubmission('riskForm', {
            successMessage: 'Risk saved successfully!',
            refreshList: 'risk-list-container',
            onSuccess: function(data) {
                // Any risk-specific success logic can go here
                console.log('Risk saved successfully');
            },
            onError: function(error) {
                console.error('Error saving risk:', error);
            }
        });
    }

    // Add form validation
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });
}); 