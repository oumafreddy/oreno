/**
 * Recommendation Modal Form JavaScript
 * Handles recommendation-specific form logic
 * Generic form submission is now handled by modal-handler.js
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('recommendationForm');
    if (!form) return;

    // Use ModalHandler for enhanced form submission handling
    if (window.ModalHandler) {
        window.ModalHandler.handleFormSubmission('recommendationForm', {
            successMessage: 'Recommendation saved successfully!',
            refreshList: 'recommendation-list-container',
            onSuccess: function(data) {
                // Any recommendation-specific success logic can go here
                console.log('Recommendation saved successfully');
            },
            onError: function(error) {
                console.error('Error saving recommendation:', error);
            }
        });
    }
}); 