/**
 * Note Modal Form JavaScript
 * Handles note-specific form logic
 * CKEditor initialization is now handled by modal-handler.js
 */

document.addEventListener('DOMContentLoaded', function() {
    // CKEditor initialization is now handled by modal-handler.js
    // for all .django_ckeditor_5 fields in modals
    
    // Handle cancel button (note-specific logic)
    const cancelBtn = document.getElementById('note-cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            const url = cancelBtn.getAttribute('data-engagement-url');
            if (url) {
                window.location.href = url;
            }
        });
    }
}); 