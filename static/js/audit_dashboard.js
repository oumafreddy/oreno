// audit_dashboard.js
// All page-specific JS for the audit dashboard should go here.
// This file is CSP-compliant and ready for future enhancements.

document.addEventListener('DOMContentLoaded', function() {
    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('audit-dashboard-vars');
    if (varsEl) {
        window.AUDIT_ENGAGEMENT_URL = varsEl.getAttribute('data-engagement-url');
        window.AUDIT_ISSUE_URL = varsEl.getAttribute('data-issue-url');
    }
    // Add more audit dashboard logic here as needed
}); 