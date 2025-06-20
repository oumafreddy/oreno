// procedure_modal_form.js
// Add your modal form JS logic here if any. If the original inline script handled form validation, AJAX, or modal events, move it here.
// If the script is empty, leave this as a placeholder for future logic. 

/**
 * Procedure Modal Form JavaScript
 * Handles procedure form submission and modal interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeModalNavigation();
    initializeFormConfirmations();
});

/**
 * Initialize modal navigation handlers
 */
function initializeModalNavigation() {
    // Handle navigation buttons with data-navigate-url attribute
    document.addEventListener('click', function(event) {
        const button = event.target.closest('[data-navigate-url]');
        if (button) {
            const url = button.getAttribute('data-navigate-url');
            if (url && url !== '#') {
                window.location.href = url;
            }
        }
    });
}

/**
 * Initialize form confirmation handlers
 */
function initializeFormConfirmations() {
    // Handle form submissions with data-confirm attribute
    document.addEventListener('submit', function(event) {
        const form = event.target;
        if (form.hasAttribute('data-confirm')) {
            const confirmMessage = form.getAttribute('data-confirm');
            if (!confirmAction(confirmMessage)) {
                event.preventDefault();
                return false;
            }
        }
    });
}

/**
 * Confirm an action with a custom message
 * @param {string} message - The confirmation message
 * @returns {boolean} - True if confirmed, false otherwise
 */
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed?');
}

// Export functions for global access
window.ProcedureModalForm = {
    initializeModalNavigation,
    confirmAction
}; 