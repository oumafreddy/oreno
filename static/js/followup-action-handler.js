/**
 * Follow-up Action Handler
 * Handles form submission, validation, and modal interactions for follow-up actions
 */

(function() {
    if (window.FollowUpActionHandler) return;
    class FollowUpActionHandler {
        constructor() {
            this.initializeEventListeners();
        }

        initializeEventListeners() {
            // Handle form submission
            document.addEventListener('submit', (e) => {
                const form = e.target.closest('.followup-action-form');
                if (form) {
                    e.preventDefault();
                    this.handleFormSubmit(form);
                }
            });

            // Handle modal events
            document.addEventListener('show.bs.modal', (e) => {
                if (e.target.id === 'globalModal') {
                    this.handleModalShow(e.target);
                }
            });

            document.addEventListener('hidden.bs.modal', (e) => {
                if (e.target.id === 'globalModal') {
                    this.handleModalHidden(e.target);
                }
            });
        }

        handleFormSubmit(form) {
            // Prevent double submission
            if (form.dataset.submitted === 'true') {
                return;
            }

            // Show loading state
            const submitButton = form.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';

            // Submit form via HTMX
            htmx.trigger(form, 'submit');
        }

        handleModalShow(modal) {
            // Initialize any form-specific behaviors
            const form = modal.querySelector('.followup-action-form');
            if (form) {
                // Reset form state
                form.dataset.submitted = 'false';
                
                // Initialize any form plugins
                if (typeof CKEDITOR !== 'undefined') {
                    CKEDITOR.replaceAll('django_ckeditor_5');
                }
            }
        }

        handleModalHidden(modal) {
            // Clean up any form-specific behaviors
            const form = modal.querySelector('.followup-action-form');
            if (form) {
                // Reset form state
                form.dataset.submitted = 'false';
                
                // Clean up any form plugins
                if (typeof CKEDITOR !== 'undefined') {
                    CKEDITOR.instances.forEach(instance => {
                        if (instance.element.closest('#globalModal')) {
                            instance.destroy();
                        }
                    });
                }
            }
        }

        handleSuccessfulSubmission(form) {
            // Mark as submitted to prevent reset
            form.dataset.submitted = 'true';
            
            // Show success message
            this.showToast('Follow-up action saved successfully!', 'success');
            
            // Close modal after a short delay
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('globalModal'));
                if (modal) {
                    modal.hide();
                }
                
                // Refresh the follow-up list
                const issueId = form.querySelector('[name="issue"]')?.value;
                if (issueId) {
                    htmx.trigger('body', 'refreshFollowupList');
                }
            }, 300);
        }

        showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            
            const container = document.getElementById('toast-container') || document.body;
            container.appendChild(toast);
            
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            // Remove toast after it's hidden
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        }
    }
    window.FollowUpActionHandler = FollowUpActionHandler;
})();

// Initialize the handler when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.followUpActionHandler = new FollowUpActionHandler();
});
