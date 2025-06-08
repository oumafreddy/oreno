/**
 * Follow-up Action Handler
 * Handles form submission, validation, and modal interactions for follow-up actions
 */

class FollowUpActionHandler {
    constructor() {
        this.initEventListeners();
        this.initDatePickers();
    }

    initEventListeners() {
        // Handle form submission
        document.addEventListener('submit', (e) => {
            const form = e.target.closest('#followupactionForm');
            if (!form) return;

            this.handleFormSubmit(form, e);
        });

        // Handle modal close
        const modal = document.getElementById('followupActionModal') || document.getElementById('globalModal');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => this.handleModalClose(modal));
        }

        // Handle HTMX after request
        document.body.addEventListener('htmx:afterRequest', (evt) => this.handleHtmxAfterRequest(evt));
    }

    handleFormSubmit(form, event) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            const spinner = submitButton.querySelector('.spinner-border') || document.createElement('span');
            const btnText = submitButton.querySelector('.btn-text');
            
            if (!spinner.classList.contains('spinner-border')) {
                spinner.className = 'spinner-border spinner-border-sm me-1';
                spinner.setAttribute('role', 'status');
                spinner.setAttribute('aria-hidden', 'true');
                submitButton.insertBefore(spinner, btnText);
            }
            spinner.classList.remove('d-none');
            
            if (btnText) {
                const originalText = btnText.textContent.trim();
                btnText.textContent = 'Saving...';
                btnText.dataset.originalText = originalText;
            }
        }
    }

    handleModalClose(modal) {
        // Skip if this is an HTMX request
        if (window.htmx && window.htmx.find) return;
        
        const form = modal.querySelector('form');
        if (form) {
            // Only reset if not submitted
            if (form.dataset.submitted !== 'true') {
                form.reset();
                // Clear validation errors
                form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
                form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
            } else {
                // Reset flag for next submission
                form.dataset.submitted = 'false';
            }
            
            // Reset submit button
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = false;
                const btnText = submitButton.querySelector('.btn-text');
                if (btnText && btnText.dataset.originalText) {
                    btnText.textContent = btnText.dataset.originalText;
                }
            }
        }
        
        // Clear dynamic modal content after animation completes
        if (modal.id === 'globalModal') {
            setTimeout(() => {
                const modalContent = modal.querySelector('.modal-content');
                if (modalContent) modalContent.innerHTML = '';
            }, 300);
        }
    }

    handleHtmxAfterRequest(evt) {
        const form = evt.detail.elt?.closest('form');
        if (!form || form.id !== 'followupactionForm') return;

        // Handle successful submission
        if (evt.detail.successful) {
            this.handleSuccessfulSubmission(form);
        } else {
            this.handleFailedSubmission(evt.detail.xhr);
        }
    }

    handleSuccessfulSubmission(form) {
        // Mark as submitted to prevent reset
        form.dataset.submitted = 'true';
        
        // Show success message
        this.showToast('Follow-up action saved successfully!', 'success');
        
        // Close modal after a short delay
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(
                document.getElementById('followupActionModal') || 
                document.getElementById('globalModal')
            );
            if (modal) modal.hide();
            if (typeof window.cleanupModalOverlays === 'function') {
                setTimeout(window.cleanupModalOverlays, 350);
            }
            // Refresh the follow-up list
            const issueId = form.querySelector('[name="issue"]')?.value;
            if (issueId) {
                htmx.ajax('GET', `/audit/followupaction/list/?issue_id=${issueId}`, {
                    target: '#followup-list-container',
                    swap: 'innerHTML'
                });
            }
        }, 300);
    }

    handleFailedSubmission(xhr) {
        try {
            const response = JSON.parse(xhr.responseText);
            let errorMessage = 'An error occurred while saving the follow-up action.';
            
            if (response.errors) {
                errorMessage = Object.values(response.errors).join(' ');
            } else if (response.message) {
                errorMessage = response.message;
            }
            
            this.showToast(errorMessage, 'danger');
        } catch (e) {
            console.error('Error parsing error response:', e);
            this.showToast('An unexpected error occurred. Please try again.', 'danger');
        }
    }

    initDatePickers() {
        // Initialize date pickers if available
        if (typeof flatpickr !== 'undefined') {
            flatpickr("input[type='date']", {
                dateFormat: "Y-m-d",
                allowInput: true,
                defaultDate: 'today'
            });
        }
    }

    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast show bg-${type} text-white mb-2`;
        toast.role = 'alert';
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // Add toast content
        toast.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Auto-remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 150);
        }, 5000);
        
        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 5000 });
        bsToast.show();
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize the handler when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    new FollowUpActionHandler();
});
