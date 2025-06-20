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
        UIUtils.showToast('Success', 'Follow-up action saved successfully!', 'success');
        
        // Close modal after a short delay
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(
                document.getElementById('followupActionModal') || 
                document.getElementById('globalModal')
            );
            if (modal) modal.hide();

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
            
            UIUtils.showToast('Error', errorMessage, 'danger');
        } catch (e) {
            console.error('Error parsing error response:', e);
            UIUtils.showToast('Error', 'An unexpected error occurred. Please try again.', 'danger');
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

}

// Initialize the handler when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    new FollowUpActionHandler();
});
