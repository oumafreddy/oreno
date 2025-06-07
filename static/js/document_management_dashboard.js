// document_management_dashboard.js
// All page-specific JS for the document management dashboard should go here.
// This file is CSP-compliant and ready for future enhancements.

document.addEventListener('DOMContentLoaded', function() {
    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('document-management-dashboard-vars');
    if (varsEl) {
        window.DOCUMENT_MANAGEMENT_STATUS_URL = varsEl.getAttribute('data-status-url');
        window.DOCUMENT_MANAGEMENT_UPLOADS_URL = varsEl.getAttribute('data-uploads-url');
    }
    // Add more document management dashboard logic here as needed
}); 