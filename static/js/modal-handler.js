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
 * 
 * PUBLIC API:
 * -----------
 * ModalHandler.showModal(modalId) - Show a modal by ID
 * ModalHandler.hideModal(modalId) - Hide a modal by ID  
 * ModalHandler.getInstance(modalId) - Get modal instance
 * ModalHandler.cleanupContent(modalBody) - Clean modal content
 * ModalHandler.initializeComponents(modalBody) - Initialize form components
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
    });

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
        }
    };
})();
