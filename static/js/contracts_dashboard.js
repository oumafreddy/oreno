// contracts_dashboard.js
// All page-specific JS for the contracts dashboard should go here.
// This file is CSP-compliant and ready for future enhancements.

document.addEventListener('DOMContentLoaded', function() {
    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('contracts-dashboard-vars');
    if (varsEl) {
        window.CONTRACTS_STATUS_URL = varsEl.getAttribute('data-status-url');
        window.CONTRACTS_TYPE_URL = varsEl.getAttribute('data-type-url');
        window.CONTRACTS_PARTY_URL = varsEl.getAttribute('data-party-url');
        window.CONTRACTS_MILESTONE_TYPE_URL = varsEl.getAttribute('data-milestone-type-url');
        window.CONTRACTS_MILESTONE_STATUS_URL = varsEl.getAttribute('data-milestone-status-url');
        window.CONTRACTS_EXPIRY_URL = varsEl.getAttribute('data-expiry-url');
    }
    // Add more contracts dashboard logic here as needed
}); 