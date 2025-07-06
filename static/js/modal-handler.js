/**
 * Oreno GRC Modal Handler
 * A comprehensive modal management system for the entire application
 * Handles Bootstrap modals, HTMX integration, form submissions, and dynamic content
 * 
 * USAGE:
 * ------
 * 1. Include this script in your base template
 * 2. Use Bootstrap modal triggers: data-bs-toggle="modal" data-bs-target="#modalId"
 * 3. For HTMX modals, target the modal body: hx-target="#modal-body"
 * 4. Access modal functions: window.ModalHandler.showModal('modalId')
 * 
 * FEATURES:
 * ---------
 * - Automatic modal instance management
 * - HTMX form submission handling with loading states
 * - Content cleanup to prevent duplication
 * - Dynamic content observer for new modals
 * - Bootstrap 5 compatibility with fallbacks
 * - Form component initialization (Select2, datepickers, etc.)
 * - Error state management
 * - Modal overlay cleanup
 * - Generic navigation handling
 * - Form confirmation dialogs
 * - Toast notification system
 * - Enhanced form submission with spinner states
 * 
 * PUBLIC API:
 * -----------
 * ModalHandler.showModal(modalId) - Show a modal by ID
 * ModalHandler.hideModal(modalId) - Hide a modal by ID  
 * ModalHandler.getInstance(modalId) - Get modal instance
 * ModalHandler.cleanupContent(modalBody) - Clean modal content
 * ModalHandler.initializeComponents(modalBody) - Initialize form components
 * ModalHandler.showNotification(message, type) - Show toast notification
 * ModalHandler.confirmAction(message) - Show confirmation dialog
 * ModalHandler.handleFormSubmission(formId, options) - Handle form submission
 * 
 * DEPENDENCIES:
 * -------------
 * - Bootstrap 5 (with fallback for older versions)
 * - HTMX (for dynamic content loading)
 * - jQuery (optional, for Select2 and other components)
 */

// Self-executing function to avoid global namespace pollution
(function() {
    // Store modal instances to prevent duplicate instantiation
    const modalInstances = new Map();
    
    // When DOM is fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        setupModalHandling();
        setupBootstrapModals();
        initializeDynamicContentObserver();
        cleanupModalOverlays();
        setupGenericModalFeatures();
    });

    /**
     * Setup generic modal features (navigation, confirmations, notifications)
     */
    function setupGenericModalFeatures() {
        // Initialize modal navigation handlers
        initializeModalNavigation();
        
        // Initialize form confirmation handlers
        initializeFormConfirmations();
        
        // Initialize notification system
        initializeNotificationSystem();
        
        // Initialize enhanced form submission handling
        initializeEnhancedFormSubmission();
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
     * Initialize notification system
     */
    function initializeNotificationSystem() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }
    }

    /**
     * Initialize enhanced form submission handling
     */
    function initializeEnhancedFormSubmission() {
        // Handle form submissions with spinner states
        document.addEventListener('htmx:beforeRequest', function(event) {
            const form = event.detail.elt.closest('form');
            if (form && form.closest('.modal')) {
                const submitButton = form.querySelector('[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    const originalText = submitButton.textContent;
                    submitButton.setAttribute('data-original-text', originalText);
                    
                    // Add spinner if not present
                    if (!submitButton.querySelector('.spinner-border')) {
                        const spinner = document.createElement('span');
                        spinner.className = 'spinner-border spinner-border-sm ms-2';
                        spinner.setAttribute('role', 'status');
                        spinner.innerHTML = '<span class="visually-hidden">Loading...</span>';
                        submitButton.appendChild(spinner);
                    }
                    
                    // Update button text
                    submitButton.textContent = 'Saving...';
                }
            }
        });

        // Handle form submission completion
        document.addEventListener('htmx:afterRequest', function(event) {
            const form = event.detail.elt.closest('form');
            if (form && form.closest('.modal')) {
                const submitButton = form.querySelector('[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = false;
                    
                    // Remove spinner
                    const spinner = submitButton.querySelector('.spinner-border');
                    if (spinner) {
                        spinner.remove();
                    }
                    
                    // Restore original text
                    const originalText = submitButton.getAttribute('data-original-text');
                    if (originalText) {
                        submitButton.textContent = originalText;
                        submitButton.removeAttribute('data-original-text');
                    }
                }
            }
        });
    }

    /**
     * Setup the main modal handling functionality
     */
    function setupModalHandling() {
        // Handle modal trigger clicks (legacy data-toggle)
        document.body.addEventListener('click', function(event) {
            const trigger = event.target.closest('[data-toggle="modal"]');
            if (trigger) {
                event.preventDefault();
                
                const targetSelector = trigger.getAttribute('data-target') || trigger.getAttribute('href');
                if (targetSelector) {
                    const modal = document.querySelector(targetSelector);
                    if (modal) {
                        const modalInstance = getOrCreateModalInstance(modal);
                        modalInstance.show();
                    }
                }
                
                // Reset any previous errors or state
                const modalBody = document.getElementById('modal-body');
                if (modalBody) {
                    cleanupModalContent(modalBody);
                }
            }
        });
        
        // Handle Bootstrap 5 modal triggers
        document.body.addEventListener('click', function(event) {
            const trigger = event.target.closest('[data-bs-toggle="modal"]');
            if (trigger) {
                // Skip AI Assistant triggers - handled by ai_assistant.js
                if (trigger.getAttribute('data-bs-target') === '#aiAssistantModal') {
                    return;
                }
                
                event.preventDefault();
                
                const targetSelector = trigger.getAttribute('data-bs-target') || trigger.getAttribute('href');
                if (targetSelector) {
                    const modal = document.querySelector(targetSelector);
                    if (modal && modal.classList.contains('modal')) {
                        const modalInstance = getOrCreateModalInstance(modal);
                        if (modalInstance) {
                            modalInstance.show();
                        }
                    }
                }
                
                // Reset any previous errors or state
                const modalBody = document.getElementById('modal-body');
                if (modalBody) {
                    cleanupModalContent(modalBody);
                }
            }
        });
        
        // After HTMX content is loaded into a modal
        document.body.addEventListener('htmx:afterSwap', function(event) {
            if (event.detail.target && (event.detail.target.id === 'modal-body' || event.detail.target.id === 'globalModal-body')) {
                // More comprehensive cleanup of modal content to prevent duplication
                cleanupModalContent(event.detail.target);
                
                // Initialize any special components within the modal content
                initializeModalComponents(event.detail.target);
            }
        });
        
        // Handle modal close events to clean up CKEditor instances
        document.body.addEventListener('hidden.bs.modal', function(event) {
            const modal = event.target;
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                // Clean up CKEditor instances when modal is closed
                if (typeof ClassicEditor !== 'undefined') {
                    try {
                        const ckeditorElements = modalBody.querySelectorAll('.django_ckeditor_5');
                        ckeditorElements.forEach(element => {
                            if (element.ckeditorInstance) {
                                element.ckeditorInstance.destroy();
                                element.ckeditorInstance = null;
                            }
                        });
                    } catch (error) {
                        console.warn('Error cleaning up CKEditor instances on modal close:', error);
                    }
                }
            }
        });
        
        // Handle HTMX form submission in modals
        document.body.addEventListener('htmx:beforeSend', function(event) {
            const form = event.detail.elt.closest('form');
            if (form && form.closest('.modal')) {
                // Add loading spinner to submit button
                const submitButton = form.querySelector('[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    if (!submitButton.querySelector('.spinner-border')) {
                        const spinner = document.createElement('span');
                        spinner.className = 'spinner-border spinner-border-sm ms-2';
                        spinner.setAttribute('role', 'status');
                        spinner.innerHTML = '<span class="visually-hidden">Loading...</span>';
                        submitButton.appendChild(spinner);
                    }
                }
            }
        });
        
        // Handle successful HTMX submissions in modals
        document.body.addEventListener('htmx:afterRequest', function(event) {
            const form = event.detail.elt.closest('form');
            if (form && form.closest('.modal')) {
                const submitButton = form.querySelector('[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = false;
                    const spinner = submitButton.querySelector('.spinner-border');
                    if (spinner) {
                        spinner.remove();
                    }
                }
                
                // Check if we have a success response and need to close the modal
                if (event.detail.successful && !event.detail.xhr.response.includes('is-invalid')) {
                    // Success handling - close modal after successful form submission
                    const modal = form.closest('.modal');
                    if (modal) {
                        try {
                            const modalInstance = getOrCreateModalInstance(modal);
                            modalInstance.hide();
                        } catch (error) {
                            console.warn('Modal hide failed, trying alternative method', error);
                            modal.classList.remove('show');
                            modal.style.display = 'none';
                        }
                    }
                }
            }
        });
        
        // Handle modal responses from main.js (JSON responses)
        document.body.addEventListener('htmx:afterRequest', function(evt) {
            // Only handle modal responses
            if (evt.detail && evt.detail.successful && evt.detail.target && evt.detail.target.closest && evt.detail.target.closest('#modal-body')) {
                try {
                    var contentType = evt.detail.xhr.getResponseHeader('content-type') || '';
                    if (contentType.includes('application/json')) {
                        var data = JSON.parse(evt.detail.xhr.responseText);
                        if (data && data.form_is_valid) {
                            var mainModal = document.getElementById('mainModal');
                            if (mainModal && typeof bootstrap !== 'undefined') {
                                var bsModal = bootstrap.Modal.getInstance(mainModal);
                                if (bsModal) bsModal.hide();
                            }
                            // Optionally refresh lists if present
                            if (data.html_list) {
                                var noteList = document.getElementById('note-list-container');
                                if (noteList) noteList.innerHTML = data.html_list;
                            }
                        }
                    }
                    // If not JSON, do nothing: HTMX will swap in the HTML form
                } catch (e) {
                    console.error('Error handling modal response:', e);
                }
            }
        });

        // --- CKEditor5 Robust Initialization for Modal Forms ---
        // Helper: Add .ckeditor-richtext class to all CKEditor fields (if not present)
        function ensureCkeditorClass(modal) {
            if (!modal) return;
            const ckeditors = modal.querySelectorAll('.django_ckeditor_5');
            ckeditors.forEach(el => {
                if (!el.classList.contains('ckeditor-richtext')) {
                    el.classList.add('ckeditor-richtext');
                }
            });
        }

        // Force CKEditor5 initialization after modal content loads (shown.bs.modal)
        document.body.addEventListener('shown.bs.modal', function(event) {
            const modal = event.target;
            if (modal && modal.classList.contains('modal')) {
                ensureCkeditorClass(modal);
                if (typeof ClassicEditor !== 'undefined') {
                    const ckeditorElements = modal.querySelectorAll('.django_ckeditor_5, .ckeditor-richtext');
                    ckeditorElements.forEach(element => {
                        if (!element.ckeditorInstance) {
                            ClassicEditor.create(element, {})
                                .then(editor => {
                                    element.ckeditorInstance = editor;
                                })
                                .catch(error => {
                                    console.warn('Error initializing CKEditor in modal:', error);
                                });
                        }
                    });
                }
            }
        });

        // Force CKEditor5 initialization after HTMX swaps in modal content
        // (e.g., after AJAX loads modal body)
        document.body.addEventListener('htmx:afterSwap', function(event) {
            if (event.detail.target && (event.detail.target.id === 'modal-body' || event.detail.target.classList.contains('modal-body'))) {
                ensureCkeditorClass(event.detail.target);
                if (typeof ClassicEditor !== 'undefined') {
                    const ckeditorElements = event.detail.target.querySelectorAll('.django_ckeditor_5, .ckeditor-richtext');
                    ckeditorElements.forEach(element => {
                        if (!element.ckeditorInstance) {
                            ClassicEditor.create(element, {})
                                .then(editor => {
                                    element.ckeditorInstance = editor;
                                })
                                .catch(error => {
                                    console.warn('Error initializing CKEditor in modal after HTMX swap:', error);
                                });
                        }
                    });
                }
            }
        });
    }
    
    /**
     * Function to thoroughly clean up modal content
     */
    function cleanupModalContent(modalBody) {
        // 1. Clean up CKEditor instances to prevent duplication errors
        if (typeof ClassicEditor !== 'undefined') {
            try {
                // Destroy any existing CKEditor 5 instances in the modal
                const ckeditorElements = modalBody.querySelectorAll('.django_ckeditor_5');
                ckeditorElements.forEach(element => {
                    const editorId = element.id;
                    // Check if there's an editor instance attached to this element
                    if (element.ckeditorInstance) {
                        element.ckeditorInstance.destroy();
                        element.ckeditorInstance = null;
                    }
                });
            } catch (error) {
                console.warn('Error cleaning up CKEditor instances:', error);
            }
        }
        
        // 2. Remove any nested modal headers/footers to prevent duplication
        const nestedHeaders = modalBody.querySelectorAll('.modal-header');
        const nestedFooters = modalBody.querySelectorAll('.modal-footer');
        const nestedModals = modalBody.querySelectorAll('.modal-dialog, .modal-content');
        const navbars = modalBody.querySelectorAll('nav.navbar, .navbar, header, footer');
        const footerElements = modalBody.querySelectorAll('footer, .footer');
        
        // Remove navigation and footer elements
        navbars.forEach(nav => nav.remove());
        footerElements.forEach(footer => footer.remove());
        
        // Remove nested modal elements if they exist within another modal
        if (modalBody.closest('.modal')) {
            nestedHeaders.forEach(header => {
                if (header !== modalBody.closest('.modal').querySelector('.modal-header')) {
                    header.remove();
                }
            });
            nestedFooters.forEach(footer => {
                if (footer !== modalBody.closest('.modal').querySelector('.modal-footer')) {
                    footer.remove();
                }
            });
            nestedModals.forEach(modal => {
                if (modal !== modalBody.closest('.modal-dialog, .modal-content')) {
                    modal.remove();
                }
            });
        }
        
        // 3. Clean up any leftover HTMX indicators
        const indicators = modalBody.querySelectorAll('.htmx-indicator');
        indicators.forEach(indicator => indicator.remove());
        
        // 4. Reset form states
        const forms = modalBody.querySelectorAll('form');
        forms.forEach(form => {
            form.reset();
            const invalidFields = form.querySelectorAll('.is-invalid');
            invalidFields.forEach(field => field.classList.remove('is-invalid'));
            const feedbackElements = form.querySelectorAll('.invalid-feedback');
            feedbackElements.forEach(element => element.remove());
        });
    }
    
    /**
     * Function to initialize any special components within modal content
     */
    function initializeModalComponents(modalBody) {
        // Get the parent modal element
        const modalElement = findParentModal(modalBody);
        if (modalElement) {
            // Ensure modal is shown, Bootstrap 5 method
            const modalInstance = getOrCreateModalInstance(modalElement);
            
            // Initialize any form elements in the new content
            initializeFormElements(modalBody);
            
            // Show modal if it's not already visible
            if (!modalElement.classList.contains('show')) {
                try {
                    modalInstance.show();
                } catch (error) {
                    console.warn('Modal show failed, trying alternative method', error);
                    // Fallback handling
                    modalElement.classList.add('show');
                    modalElement.style.display = 'block';
                }
            }
        }
    }
    
    /**
     * Initialize components inside modal forms
     */
    function initializeFormElements(target) {
        // Initialize CKEditor instances
        if (typeof ClassicEditor !== 'undefined') {
            try {
                const ckeditorElements = target.querySelectorAll('.django_ckeditor_5');
                ckeditorElements.forEach(element => {
                    const editorId = element.id;
                    // Only initialize if not already initialized
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
            } catch (error) {
                console.warn('Error initializing CKEditor instances:', error);
            }
        }

        // Find select2 elements and initialize them
        if (window.jQuery && jQuery().select2) {
            jQuery(target).find('select.select2').each(function() {
                jQuery(this).select2({
                    dropdownParent: jQuery('#globalModal')
                });
            });
        }

        // Initialize any date pickers
        if (window.flatpickr) {
            target.querySelectorAll('.datepicker').forEach(function(el) {
                flatpickr(el, {
                    // Your date picker options
                });
            });
        }
        
        // Initialize any other form components
        if (window.jQuery) {
            // Initialize tooltips
            jQuery(target).find('[data-bs-toggle="tooltip"]').tooltip();
            
            // Initialize popovers
            jQuery(target).find('[data-bs-toggle="popover"]').popover();
        }
    }
    
    /**
     * Setup Bootstrap modals on the page
     */
    function setupBootstrapModals() {
        // Find all elements with data-bs-toggle="modal" attribute
        document.querySelectorAll('[data-bs-toggle="modal"]').forEach(function(trigger) {
            // Skip AI Assistant triggers - handled by ai_assistant.js
            if (trigger.getAttribute('data-bs-target') === '#aiAssistantModal') {
                return;
            }
            
            trigger.addEventListener('click', function(event) {
                event.preventDefault();
                
                const targetSelector = trigger.getAttribute('data-bs-target') || trigger.getAttribute('href');
                if (targetSelector) {
                    const modal = document.querySelector(targetSelector);
                    if (modal) {
                        const modalInstance = getOrCreateModalInstance(modal);
                        if (modalInstance) {
                            modalInstance.show();
                        }
                    }
                }
            });
        });
        
        // Setup all modals except AI Assistant modal (handled by ai_assistant.js)
        document.querySelectorAll('.modal').forEach(function(modal) {
            // Skip AI Assistant modal - it's handled by ai_assistant.js
            if (modal.id === 'aiAssistantModal') {
                return;
            }
            
            // Skip if already has an instance
            if (modalInstances.has(modal)) {
                return;
            }
            
            try {
                getOrCreateModalInstance(modal);
            } catch (error) {
                console.warn('Failed to initialize modal:', modal.id, error);
            }
        });
    }
    
    /**
     * Initialize MutationObserver to handle dynamically added content
     */
    function initializeDynamicContentObserver() {
        // Create a new observer
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    // Check for new modal triggers
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            // Initialize new modal triggers
                            const newTriggers = node.querySelectorAll ? 
                                node.querySelectorAll('[data-bs-toggle="modal"]') : [];
                            
                            if (newTriggers.length > 0) {
                                setupBootstrapModals();
                            }
                            
                            // Initialize new modals
                            const newModals = node.querySelectorAll ? 
                                node.querySelectorAll('.modal') : [];
                            
                            if (newModals.length > 0) {
                                newModals.forEach(function(modal) {
                                    getOrCreateModalInstance(modal);
                                });
                            }
                        }
                    });
                }
            });
        });
        
        // Start observing the document
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // Utility functions
    
    /**
     * Find the parent modal element of a given element
     */
    function findParentModal(element) {
        let current = element;
        while (current && current !== document) {
            if (current.classList.contains('modal')) {
                return current;
            }
            current = current.parentNode;
        }
        return null;
    }
    
    /**
     * Get or create a Bootstrap modal instance
     */
    function getOrCreateModalInstance(modalElement) {
        if (!modalElement || !modalElement.classList.contains('modal')) {
            console.warn('Invalid modal element provided to getOrCreateModalInstance');
            return null;
        }
        
        if (modalInstances.has(modalElement)) {
            return modalInstances.get(modalElement);
        }
        
        let instance;
        try {
            if (window.bootstrap && window.bootstrap.Modal) {
                // Check if modal already has an instance
                const existingInstance = bootstrap.Modal.getInstance(modalElement);
                if (existingInstance) {
                    modalInstances.set(modalElement, existingInstance);
                    return existingInstance;
                }
                
                // Create new instance with proper configuration
                instance = new bootstrap.Modal(modalElement, {
                    backdrop: true,
                    keyboard: true,
                    focus: true
                });
                
                // Patch hide to cleanup overlays
                const origHide = instance.hide.bind(instance);
                instance.hide = function() {
                    origHide();
                    setTimeout(cleanupModalOverlays, 350); // after animation
                };
            } else {
                instance = {
                    show: function() {
                        modalElement.classList.add('show');
                        modalElement.style.display = 'block';
                    },
                    hide: function() {
                        modalElement.classList.remove('show');
                        modalElement.style.display = 'none';
                        cleanupModalOverlays();
                    }
                };
            }
            modalInstances.set(modalElement, instance);
            return instance;
        } catch (error) {
            console.error('Error creating modal instance:', error);
            // Return a fallback instance
            return {
                show: function() {
                    modalElement.classList.add('show');
                    modalElement.style.display = 'block';
                },
                hide: function() {
                    modalElement.classList.remove('show');
                    modalElement.style.display = 'none';
                    cleanupModalOverlays();
                }
            };
        }
    }
    
    // Utility to clean up modal overlays and body class
    function cleanupModalOverlays() {
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        document.body.classList.remove('modal-open');
        document.body.style = '';
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
            const toast = createToastElement('Oreno GRC', message, type);
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

    /**
     * Handle form submission with enhanced features
     * @param {string} formId - The form ID
     * @param {object} options - Options for form handling
     */
    function handleFormSubmission(formId, options = {}) {
        const form = document.getElementById(formId);
        if (!form) {
            console.error(`Form with ID '${formId}' not found`);
            return;
        }

        const {
            onSuccess,
            onError,
            showSpinner = true,
            closeModal = true,
            refreshList = null,
            successMessage = 'Form submitted successfully!'
        } = options;

        // Add form submission handler
        form.addEventListener('htmx:afterRequest', function(event) {
            try {
                const detail = event.detail;
                const xhr = detail.xhr;
                const contentType = xhr.getResponseHeader('content-type') || '';
                
                if (contentType.includes('application/json')) {
                    const data = JSON.parse(xhr.responseText);
                    
                    if (data.success || data.form_is_valid) {
                        // Close the modal if requested
                        if (closeModal) {
                            closeCurrentModal();
                        }
                        
                        // Update the list if provided
                        if (refreshList && data.html_list) {
                            updateContentContainer(data.html_list, refreshList);
                        }
                        
                        // Show success message
                        if (successMessage) {
                            showNotification(successMessage, 'success');
                        }
                        
                        // Call custom success handler
                        if (onSuccess) {
                            onSuccess(data);
                        }
                        
                        // Redirect if provided
                        if (data.redirect) {
                            window.location.href = data.redirect;
                        }
                    } else if (data.html_form) {
                        // Replace the modal content with the form containing errors
                        updateModalContent(data.html_form);
                        
                        // Call custom error handler
                        if (onError) {
                            onError(data);
                        }
                    }
                }
            } catch (e) {
                console.warn('Error handling form response:', e);
                if (onError) {
                    onError(e);
                }
            }
        });

        // Handle form submission errors
        form.addEventListener('htmx:responseError', function(event) {
            console.error('Form submission error:', event.detail);
            showNotification('An error occurred while submitting the form.', 'error');
            if (onError) {
                onError(event.detail);
            }
        });
    }
    
    // Public API
    window.ModalHandler = {
        showModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                const instance = getOrCreateModalInstance(modal);
                instance.show();
            }
        },
        
        hideModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                const instance = getOrCreateModalInstance(modal);
                instance.hide();
            }
        },
        
        getInstance: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                return getOrCreateModalInstance(modal);
            }
            return null;
        },
        
        cleanupContent: function(modalBody) {
            cleanupModalContent(modalBody);
        },
        
        initializeComponents: function(modalBody) {
            initializeFormElements(modalBody);
        },

        showNotification: function(message, type = 'info') {
            showNotification(message, type);
        },

        confirmAction: function(message) {
            return confirmAction(message);
        },

        handleFormSubmission: function(formId, options) {
            handleFormSubmission(formId, options);
        },

        closeCurrentModal: function() {
            closeCurrentModal();
        },

        updateContentContainer: function(html, targetId) {
            updateContentContainer(html, targetId);
        },

        updateModalContent: function(html) {
            updateModalContent(html);
        },

        submitModalForm: function(formId) {
            submitModalForm(formId);
        }
    };
})();
