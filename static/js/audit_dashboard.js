// audit_dashboard.js
// All page-specific JS for the audit dashboard should go here.
// This file is CSP-compliant and ready for future enhancements.

/**
 * Audit Dashboard JavaScript
 * Handles dashboard-specific functionality including charts, dynamic content, and form interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('audit-dashboard-vars');
    if (varsEl) {
        window.AUDIT_ENGAGEMENT_URL = varsEl.getAttribute('data-engagement-url');
        window.AUDIT_ISSUE_URL = varsEl.getAttribute('data-issue-url');
    }
    // Add more audit dashboard logic here as needed

    const dashboardCards = document.querySelectorAll('.dashboard-card');
    dashboardCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow-lg');
        });
        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow-lg');
        });
    });

    // Initialize Select2 for all select elements
    if (window.jQuery && jQuery().select2) {
        jQuery('.select2').select2();
    }
    
    // Initialize dynamic parent selection functionality
    initializeParentSelection();
    
    // Initialize HTMX filters
    initializeHtmxFilters();
});

/**
 * Dynamic Parent Selection Logic
 * Handles the parent selection modal for creating new items
 */
function initializeParentSelection() {
    // Make the function globally available
    window.openParentSelectModal = function(type, parentApiUrl, createUrlTemplate) {
        const dropdown = document.getElementById('parentSelectDropdown');
        const modal = document.getElementById('parentSelectModal');
        const continueBtn = document.getElementById('parentSelectContinueBtn');
        
        if (!dropdown || !modal || !continueBtn) {
            console.error('Parent selection modal elements not found');
            return;
        }
        
        // Clear existing options
        dropdown.innerHTML = '';
        
        // Fetch parent data
        fetch(parentApiUrl)
            .then(response => response.json())
            .then(data => {
                // Populate dropdown
                data.forEach(function(item) {
                    const option = document.createElement('option');
                    option.value = item.id;
                    option.textContent = item.text;
                    dropdown.appendChild(option);
                });
                
                // Show modal
                if (window.bootstrap && window.bootstrap.Modal) {
                    const bsModal = new window.bootstrap.Modal(modal);
                    bsModal.show();
                }
                
                // Handle continue button click
                continueBtn.onclick = function() {
                    const parentId = dropdown.value;
                    const createUrl = createUrlTemplate.replace('__PARENT_ID__', parentId);
                    
                    // Hide modal
                    if (window.bootstrap && window.bootstrap.Modal) {
                        const bsModal = window.bootstrap.Modal.getInstance(modal);
                        if (bsModal) bsModal.hide();
                    }
                    
                    // Load create form
                    fetch(createUrl)
                        .then(response => response.text())
                        .then(html => {
                            const globalModal = document.getElementById('globalModal');
                            const modalContent = globalModal.querySelector('.modal-content');
                            if (modalContent) {
                                modalContent.innerHTML = html;
                                
                                // Show the modal
                                if (window.bootstrap && window.bootstrap.Modal) {
                                    const bsModal = new window.bootstrap.Modal(globalModal);
                                    bsModal.show();
                                }
                            }
                        })
                        .catch(error => {
                            console.error('Error loading create form:', error);
                        });
                };
            })
            .catch(error => {
                console.error('Error fetching parent data:', error);
            });
    };
}

/**
 * Initialize HTMX filters for dashboard lists
 */
function initializeHtmxFilters() {
    // Handle HTMX form submissions for filtering
    document.addEventListener('htmx:afterRequest', function(event) {
        // Re-initialize Select2 after HTMX content updates
        if (window.jQuery && jQuery().select2) {
            jQuery('.select2').select2();
        }
    });
}

/**
 * Utility function to refresh dashboard data
 */
function refreshDashboardData() {
    // Refresh engagement status chart
    const engagementData = document.getElementById('engagement-status-data');
    if (engagementData) {
        // Trigger chart refresh if needed
        if (window.Plotly && window.refreshEngagementChart) {
            window.refreshEngagementChart();
        }
    }
    
    // Refresh other charts as needed
    if (window.refreshAllCharts) {
        window.refreshAllCharts();
    }
}

/**
 * Handle dashboard notifications
 */
function showDashboardNotification(message, type = 'info') {
    // Use Bootstrap toast if available
    if (window.bootstrap && window.bootstrap.Toast) {
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        const toast = createToastElement('Dashboard', message, type);
        toastContainer.appendChild(toast);
        
        const bsToast = new window.bootstrap.Toast(toast);
        bsToast.show();
    } else {
        // Fallback to alert
        alert(message);
    }
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

/**
 * Create toast element
 */
function createToastElement(title, message, type) {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    return toast;
}

// Export functions for global access
window.AuditDashboard = {
    openParentSelectModal,
    refreshDashboardData,
    showDashboardNotification
}; 