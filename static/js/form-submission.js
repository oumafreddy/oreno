/**
 * Form submission handler for modal forms
 * Provides the missing submitModalForm function used by various modal forms
 */

// Self-executing function to avoid global namespace pollution
(function() {
    // Make submitModalForm available globally
    window.submitModalForm = function(formId) {
        const form = document.getElementById(formId);
        if (!form) {
            console.error('Form not found:', formId);
            return;
        }

        // Show loading indicator if present
        const loadingSpinner = document.querySelector('.loading-spinner');
        if (loadingSpinner) {
            loadingSpinner.classList.remove('d-none');
        }

        // Disable submit button to prevent double-submission
        const submitButton = document.querySelector(`button[onclick="submitModalForm('${formId}')"]`);
        if (submitButton) {
            submitButton.disabled = true;
        }

        // Submit the form via AJAX using fetch API
        const formData = new FormData(form);

        fetch(form.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            // Check if the response is JSON or HTML
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json().then(data => {
                    if (data.form_is_valid) {
                        // Close the modal
                        const modal = document.getElementById('mainModal');
                        if (modal && typeof bootstrap !== 'undefined') {
                            const bsModal = bootstrap.Modal.getInstance(modal);
                            if (bsModal) {
                                bsModal.hide();
                            }
                        }
                        
                        // Refresh the page or update relevant content
                        if (data.redirect_url) {
                            window.location.href = data.redirect_url;
                        } else if (data.html_list) {
                            // Update list container if provided
                            const listContainer = document.querySelector(data.target_id || '#list-container');
                            if (listContainer) {
                                listContainer.innerHTML = data.html_list;
                            } else {
                                // Fallback to page reload if we can't update the list
                                window.location.reload();
                            }
                        } else {
                            // Default to page reload if no specific instruction
                            window.location.reload();
                        }
                    } else {
                        // Form has errors, update the form
                        form.innerHTML = data.html_form;
                    }
                    return {isJson: true, data};
                });
            }
            // Handle HTML response
            return response.text().then(html => ({isJson: false, html}));
        })
        .then(result => {
            if (!result.isJson) {
                // Replace the modal content with the response HTML
                const modalBody = document.getElementById('modal-body');
                if (modalBody) {
                    modalBody.innerHTML = result.html;
                }
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
        })
        .finally(() => {
            // Hide loading spinner
            if (loadingSpinner) {
                loadingSpinner.classList.add('d-none');
            }
            
            // Re-enable submit button
            if (submitButton) {
                submitButton.disabled = false;
            }
        });
    };

    // Add CSS to ensure modal footers are always visible
    const style = document.createElement('style');
    style.textContent = `
        .modal-footer {
            display: flex !important;
            justify-content: flex-end !important;
            padding: 1rem !important;
            border-top: 1px solid #dee2e6 !important;
            visible: visible !important;
            opacity: 1 !important;
        }
    `;
    document.head.appendChild(style);
})();
