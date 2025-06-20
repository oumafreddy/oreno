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
                if (typeof ClassicEditor !== 'undefined') {
                    const ckeditorElements = form.querySelectorAll('.django_ckeditor_5');
                    ckeditorElements.forEach(element => {
                        if (!element.ckeditorInstance) {
                            // Use Django's CKEditor configuration
                            ClassicEditor.create(element, {
                                // Let Django handle the configuration via CKEDITOR_5_CONFIGS
                                // This ensures consistency between server-side and client-side
                            }).then(editor => {
                                element.ckeditorInstance = editor;
                            }).catch(error => {
                                console.warn('Error initializing CKEditor:', error);
                            });
                        }
                    });
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
                if (typeof ClassicEditor !== 'undefined') {
                    const ckeditorElements = form.querySelectorAll('.django_ckeditor_5');
                    ckeditorElements.forEach(element => {
                        if (element.ckeditorInstance) {
                            element.ckeditorInstance.destroy();
                            element.ckeditorInstance = null;
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

<<<<<<< HEAD
        showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
=======
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
>>>>>>> origin/codex/add-window.showtoast-assignment
            
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            
<<<<<<< HEAD
            const container = document.getElementById('toast-container') || document.body;
            container.appendChild(toast);
            
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            // Remove toast after it's hidden
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
=======
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
>>>>>>> origin/codex/add-window.showtoast-assignment
            });
        }
    }
    window.FollowUpActionHandler = FollowUpActionHandler;
})();

<<<<<<< HEAD
// Initialize the handler when the DOM is ready
=======
}

// Initialize the handler when the DOM is fully loaded
>>>>>>> origin/codex/add-window.showtoast-assignment
document.addEventListener('DOMContentLoaded', () => {
    window.followUpActionHandler = new FollowUpActionHandler();
});
