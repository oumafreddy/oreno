/**
 * UI Utilities for Oreno GRC
 * This file provides common UI functions, like showing toast notifications.
 */

(function(window) {
    'use strict';

    /**
     * Displays a toast notification.
     * @param {string} message - The message to display in the toast.
     * @param {string} type - The type of toast (e.g., 'success', 'error', 'info').
     */
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            console.error('Toast container not found.');
            return;
        }

        const toastId = 'toast-' + Math.random().toString(36).substr(2, 9);
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type} border-0 show`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        const toastBody = document.createElement('div');
        toastBody.className = 'd-flex';
        toastBody.innerHTML = `
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        `;

        toast.appendChild(toastBody);
        toastContainer.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Expose the function to the global window object
    window.UIUtils = {
        showToast: showToast
    };

    window.UIUtils = window.UIUtils || {};
    window.UIUtils.initTooltips = function() {
        if (typeof bootstrap !== 'undefined') {
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.forEach(function (tooltipTriggerEl) {
                new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    };

})(window); 