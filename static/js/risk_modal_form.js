/**
 * Risk Modal Form JavaScript
 * Handles risk form submission, validation, and modal interactions
 * CSP-compliant and integrated with HTMX
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeRiskForm();
    initializeModalNavigation();
    initializeFormConfirmations();
});

/**
 * Initialize the risk form with HTMX event handlers
 */
function initializeRiskForm() {
    const formElement = document.getElementById('riskForm');
    if (!formElement) {
        console.warn('Risk form not found');
        return;
    }

    // Handle HTMX form submission
    formElement.addEventListener('htmx:afterRequest', function(event) {
        try {
            const detail = event.detail;
            const xhr = detail.xhr;
            const contentType = xhr.getResponseHeader('content-type') || '';
            
            if (contentType.includes('application/json')) {
                const data = JSON.parse(xhr.responseText);
                
                if (data.success) {
                    // Close the modal
                    closeCurrentModal();
                    
                    // Update the risk list if provided
                    if (data.html_list) {
                        updateContentContainer(data.html_list, 'risk-list-container');
                    }
                    
                    // Show success message
                    if (data.message) {
                        showNotification(data.message, 'success');
                    }
                    
                    // Redirect if provided
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                } else if (data.html_form) {
                    // Replace the modal content with the form containing errors
                    updateModalContent(data.html_form);
                }
            }
        } catch (e) {
            console.warn('Error handling risk form response:', e);
        }
    });

    // Handle form submission errors
    formElement.addEventListener('htmx:responseError', function(event) {
        console.error('Form submission error:', event.detail);
        showNotification('An error occurred while submitting the form.', 'error');
    });
}

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
    
    // Handle buttons with data-submit-form attribute
    document.addEventListener('click', function(event) {
        const button = event.target.closest('[data-submit-form]');
        if (button) {
            const formId = button.getAttribute('data-submit-form');
            submitModalForm(formId);
        }
    });
}

/**
 * Close the current modal
 */
function closeCurrentModal() {
    const modalEl = document.getElementById('mainModal') || 
                   document.getElementById('globalModal') || 
                   document.querySelector('.modal.show');
    
    if (modalEl && window.bootstrap && window.bootstrap.Modal) {
        const modal = window.bootstrap.Modal.getInstance(modalEl) || new window.bootstrap.Modal(modalEl);
        modal.hide();
    }
}

/**
 * Update content container with new HTML
 * @param {string} html - The HTML content to insert
 * @param {string} targetId - The ID of the target container
 */
function updateContentContainer(html, targetId) {
    const container = document.getElementById(targetId);
    if (container) {
        container.innerHTML = html;
    }
}

/**
 * Update modal content
 * @param {string} html - The HTML content to insert
 */
function updateModalContent(html) {
    const modalBody = document.getElementById('modal-body') || 
                     document.querySelector('.modal-body');
    if (modalBody) {
        modalBody.innerHTML = html;
    }
}

/**
 * Submit a modal form by ID
 * @param {string} formId - The ID of the form to submit
 */
function submitModalForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.submit();
    } else {
        console.error(`Form with ID '${formId}' not found`);
    }
}

/**
 * Confirm an action with a custom message
 * @param {string} message - The confirmation message
 * @returns {boolean} - True if confirmed, false otherwise
 */
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed?');
}

/**
 * Show a notification message
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    // Use Bootstrap toast if available
    if (window.bootstrap && window.bootstrap.Toast) {
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        const toast = createToastElement('Risk Management', message, type);
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
window.RiskModalForm = {
    initializeRiskForm,
    closeCurrentModal,
    updateContentContainer,
    updateModalContent,
    submitModalForm,
    confirmAction,
    showNotification
}; 