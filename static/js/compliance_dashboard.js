// compliance_dashboard.js
// All page-specific JS for the compliance dashboard should go here.
// This file is CSP-compliant and ready for future enhancements.

document.addEventListener('DOMContentLoaded', function() {
    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('compliance-dashboard-vars');
    if (varsEl) {
        window.COMPLIANCE_FRAMEWORK_URL = varsEl.getAttribute('data-framework-url');
        window.COMPLIANCE_OBLIGATION_URL = varsEl.getAttribute('data-obligation-url');
        window.COMPLIANCE_POLICY_EXPIRY_URL = varsEl.getAttribute('data-policy-expiry-url');
    }
    // Add more compliance dashboard logic here as needed
}); 