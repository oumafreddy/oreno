/**
 * Issue Working Paper Modal Form JavaScript
 * Handles issue working paper-specific form logic
 * Generic form submission is now handled by modal-handler.js
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('workingPaperForm');
    if (!form) return;

    // Use ModalHandler for enhanced form submission handling
    if (window.ModalHandler) {
        window.ModalHandler.handleFormSubmission('workingPaperForm', {
            successMessage: 'Working paper saved successfully!',
            refreshList: 'workingpapers-list-container',
            onSuccess: function(data) {
                // Any working paper-specific success logic can go here
                console.log('Working paper saved successfully');
            },
            onError: function(error) {
                console.error('Error saving working paper:', error);
            }
        });
    }
}); 