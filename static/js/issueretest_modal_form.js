/**
 * Issue Retest Modal Form JavaScript
 * Handles issue retest-specific form logic
 * Generic form submission is now handled by modal-handler.js
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('issueretestForm');
    if (!form) return;

    // Use ModalHandler for enhanced form submission handling
    if (window.ModalHandler) {
        window.ModalHandler.handleFormSubmission('issueretestForm', {
            successMessage: 'Retest saved successfully!',
            refreshList: 'issueretest-list-container',
            onSuccess: function(data) {
                // Any retest-specific success logic can go here
                console.log('Retest saved successfully');
            },
            onError: function(error) {
                console.error('Error saving retest:', error);
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