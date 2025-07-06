/**
 * Follow-up Action Handler
 * Handles followup-specific form logic
 * Generic modal functionality is now handled by modal-handler.js
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
                
                // CKEditor initialization is now handled by modal-handler.js
                // for all .django_ckeditor_5 fields in modals
            }
        }

        handleModalHidden(modal) {
            // Clean up any form-specific behaviors
            const form = modal.querySelector('.followup-action-form');
            if (form) {
                // Reset form state
                form.dataset.submitted = 'false';
                
                // CKEditor cleanup is now handled by modal-handler.js
            }
        }

        handleSuccessfulSubmission(form) {
            // Mark as submitted to prevent reset
            form.dataset.submitted = 'true';
            
            // Show success message using ModalHandler
            if (window.ModalHandler) {
                window.ModalHandler.showNotification('Follow-up action saved successfully!', 'success');
            }
            
            // Close modal after a short delay
            setTimeout(() => {
                if (window.ModalHandler) {
                    window.ModalHandler.closeCurrentModal();
                } else {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('globalModal'));
                    if (modal) {
                        modal.hide();
                    }
                }
                
                // Refresh the follow-up list
                const issueId = form.querySelector('[name="issue"]')?.value;
                if (issueId) {
                    htmx.trigger('body', 'refreshFollowupList');
                }
            }, 300);
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

        handleFailedSubmission(xhr) {
            try {
                const response = JSON.parse(xhr.responseText);
                let errorMessage = 'An error occurred while saving the follow-up action.';
                
                if (response.errors) {
                    errorMessage = Object.values(response.errors).flat().join(', ');
                } else if (response.message) {
                    errorMessage = response.message;
                }
                
                // Show error message using ModalHandler
                if (window.ModalHandler) {
                    window.ModalHandler.showNotification(errorMessage, 'error');
                }
            } catch (e) {
                console.error('Error parsing error response:', e);
                if (window.ModalHandler) {
                    window.ModalHandler.showNotification('An unexpected error occurred. Please try again.', 'error');
                }
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
    
    window.FollowUpActionHandler = FollowUpActionHandler;
})();

// Initialize the handler when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    window.followUpActionHandler = new FollowUpActionHandler();
});
