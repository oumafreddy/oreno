/**
 * Audit Modal Utilities
 * Common functions for modal handling across audit templates
 * CSP-compliant and reusable across all audit modals
 */

(function() {
    'use strict';

/**
     * Initializes all event listeners for the modal utilities.
     * This function is designed to be called once when the DOM is ready.
     */
    function initialize() {
        // Use event delegation for dynamically added elements
        document.body.addEventListener('click', handleModalEvents);
}

/**
     * Handles all click events within the body and delegates to specific functions.
     * @param {Event} event - The click event object.
 */
    function handleModalEvents(event) {
        const navigateButton = event.target.closest('[data-navigate-url]');
        if (navigateButton) {
            handleNavigation(navigateButton);
            return;
            }

        const backButton = event.target.closest('[data-navigate-back]');
        if (backButton) {
            event.preventDefault();
            window.history.back();
            return;
        }
    }

    /**
     * Handles navigation for elements with a data-navigate-url attribute.
     * @param {HTMLElement} element - The element that was clicked.
     */
    function handleNavigation(element) {
        const url = element.getAttribute('data-navigate-url');
        if (url && url !== '#') {
            window.location.href = url;
        }
}

    /**
     * Publicly exposed function to confirm an action.
     * @param {string} message - The confirmation message to display.
     * @returns {boolean} - True if the user confirmed, false otherwise.
     */
    function confirmAction(message) {
        return confirm(message || 'Are you sure you want to proceed?');
    }

    // Initialize listeners when the DOM is fully loaded.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        // DOMContentLoaded has already fired
        initialize();
    }

    // Expose necessary functions to the global window object.
window.AuditModalUtils = {
        confirmAction: confirmAction
    };

})(); 