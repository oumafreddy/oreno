// risk_dashboard.js
// All page-specific JS for the risk dashboard should go here.
// This file is CSP-compliant and ready for future enhancements.

document.addEventListener('DOMContentLoaded', function() {
    // Example: Add event listeners for register select if needed
    const registerSelect = document.getElementById('register-select');
    const registerForm = document.getElementById('register-filter-form');
    if (registerSelect && registerForm) {
        registerSelect.addEventListener('change', function() {
            registerForm.submit();
        });
    }
    // Add more risk dashboard logic here as needed

    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('risk-dashboard-vars');
    if (varsEl) {
        window.RISK_API_HEATMAP_URL = varsEl.getAttribute('data-heatmap-url');
        window.RISK_API_ASSESSMENT_TIMELINE_URL = varsEl.getAttribute('data-assessment-timeline-url');
        window.RISK_SELECTED_REGISTER = varsEl.getAttribute('data-selected-register');
    }
}); 