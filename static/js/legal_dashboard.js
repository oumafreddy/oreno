// legal_dashboard.js
// All page-specific JS for the legal dashboard should go here.
// This file is CSP-compliant and ready for future enhancements.

document.addEventListener('DOMContentLoaded', function() {
    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('legal-dashboard-vars');
    if (varsEl) {
        window.LEGAL_CASE_STATUS_URL = varsEl.getAttribute('data-case-status-url');
        window.LEGAL_TASK_STATUS_URL = varsEl.getAttribute('data-task-status-url');
    }
    // Add more legal dashboard logic here as needed
}); 