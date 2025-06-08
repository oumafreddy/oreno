/**
 * Oreno GRC Modal Handler
 * A robust solution for handling modal functionality across the application
 * Addresses multiple browser compatibility issues and error prevention
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
        // Handle modal trigger clicks
        document.body.addEventListener('click', function(event) {
            const trigger = event.target.closest('[data-toggle="modal"]');
            if (trigger) {
                event.preventDefault();
                
                const targetSelector = trigger.getAttribute('data-target') || trigger.getAttribute('href');
                if (targetSelector) {
                    // Find the modal
                    const modal = document.querySelector(targetSelector);
                    if (modal) {
                        const modalInstance = getOrCreateModalInstance(modal);
                        modalInstance.show();
                    }
                }
                
                // Reset any previous errors or state
                const modalBody = document.getElementById('modal-body');
                if (modalBody) {
                    // Clear any previous error states
                    const errorElements = modalBody.querySelectorAll('.is-invalid, .invalid-feedback');
                    errorElements.forEach(el => {
                        if (el.classList.contains('is-invalid')) {
                            el.classList.remove('is-invalid');
                        } else {
                            el.remove();
                        }
                    });
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
        
        // Function to thoroughly clean up modal content
        function cleanupModalContent(modalBody) {
            // 1. Remove any nested modal headers/footers to prevent duplication
            const nestedHeaders = modalBody.querySelectorAll('.modal-header');
            const nestedFooters = modalBody.querySelectorAll('.modal-footer');
            const nestedModals = modalBody.querySelectorAll('.modal-dialog, .modal-content');
            const navbars = modalBody.querySelectorAll('nav.navbar');
            const footers = modalBody.querySelectorAll('footer');
            
            // Remove ALL headers and footers from the loaded content - the main modal already has these
            nestedHeaders.forEach(header => header.parentNode.removeChild(header));
            nestedFooters.forEach(footer => footer.parentNode.removeChild(footer));
            
            // Remove any full modal structures that might have been included
            nestedModals.forEach(modal => modal.parentNode.removeChild(modal));
            
            // Remove navigation bars and page footers that shouldn't be in a modal
            navbars.forEach(navbar => navbar.parentNode.removeChild(navbar));
            footers.forEach(footer => footer.parentNode.removeChild(footer));
            
            // 2. Check for and fix duplicated form elements (can happen with some templates)
            const forms = modalBody.querySelectorAll('form');
            if (forms.length > 1) {
                // Keep only the primary form
                for (let i = 1; i < forms.length; i++) {
                    const formContent = forms[i].innerHTML;
                    forms[0].innerHTML += formContent;
                    forms[i].parentNode.removeChild(forms[i]);
                }
            }
        }
        
        // Function to initialize any special components within modal content
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
        
        // Handle HTMX form submission in modals
        document.body.addEventListener('htmx:beforeSend', function(event) {
            const form = event.detail.elt.closest('form');
            if (form && form.closest('.modal')) {
                // Add any pre-submission logic here
                // For example, adding a loading spinner
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
                    // Success handling - e.g., close modal after successful form submission
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
    }
    
    /**
     * Initialize components inside modal forms
     */
    function initializeFormElements(target) {
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
    }
    
    /**
     * Setup Bootstrap modals on the page
     */
    function setupBootstrapModals() {
        // Find all elements with data-bs-toggle="modal" attribute
        document.querySelectorAll('[data-bs-toggle="modal"]').forEach(function(trigger) {
            trigger.addEventListener('click', function(event) {
                event.preventDefault();
                
                const targetSelector = trigger.getAttribute('data-bs-target') || trigger.getAttribute('href');
                if (targetSelector) {
                    const modal = document.querySelector(targetSelector);
                    if (modal) {
                        const modalInstance = getOrCreateModalInstance(modal);
                        modalInstance.show();
                    }
                }
            });
        });
        
        // Setup all modals
        document.querySelectorAll('.modal').forEach(function(modal) {
            getOrCreateModalInstance(modal);
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
        if (modalInstances.has(modalElement)) {
            return modalInstances.get(modalElement);
        }
        let instance;
        try {
            if (window.bootstrap && window.bootstrap.Modal) {
                instance = new bootstrap.Modal(modalElement);
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
        }
    };
})();
