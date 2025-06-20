// static/js/main.js
/**
 * Core Application Initialization
 */
(function() {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        if (!document.body) return;
        initCSRFHandling();
        initUIComponents();
        initErrorHandling();
        initHTMXHandling();
    });

    function initCSRFHandling() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            // Set up CSRF token for all AJAX requests
            document.addEventListener('htmx:configRequest', function(evt) {
                evt.detail.headers['X-CSRFToken'] = csrfToken;
            });
        } else {
            console.warn('CSRF token not found');
        }
    }

<<<<<<< HEAD
    function initUIComponents() {
        // Check if Bootstrap is available
        if (typeof bootstrap !== 'undefined') {
            // Initialize tooltips
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
=======
/**
 * UI Components Initialization
 */
function initUIComponents() {
    // Bootstrap component initialization
    UIUtils.initTooltips();
>>>>>>> origin/codex/add-window.showtoast-assignment

            // Initialize popovers
            const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
            popoverTriggerList.map(function(popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        } else {
            console.warn('Bootstrap not loaded');
        }
    }

    function initErrorHandling() {
        // Global error handler
        window.addEventListener('error', function(event) {
            // Suppress known errors that don't need user notification
            const suppressedErrors = [
                'Content Security Policy',
                'Script redeclaration',
                'document.body is null',
                'Cannot read properties of undefined (reading \'backdrop\')',  // Bootstrap modal error
                'this._config is undefined'  // Bootstrap modal error variant
            ];
            
            if (suppressedErrors.some(err => event.message.includes(err))) {
                return;
            }

            // Show error toast if Bootstrap is available
            if (typeof bootstrap !== 'undefined') {
                showToast('Error', event.message, 'danger');
            }
            
            console.error('Global error:', event);
        });
    }

    function initHTMXHandling() {
        // Handle HTMX errors
        document.addEventListener('htmx:error', function(evt) {
            const error = evt.detail.error;
            if (error && error.message) {
                showToast('Error', error.message, 'danger');
            }
        });

        // Handle HTMX target errors
        document.addEventListener('htmx:targetError', function(evt) {
            console.warn('HTMX target error:', evt.detail);
            // Don't show toast for target errors as they're usually handled by the application
        });

        document.body.addEventListener('htmx:afterSwap', function(event) {
            const trigger = event.detail.xhr.getResponseHeader('HX-Trigger');
            if (trigger) {
                try {
                    const triggerData = JSON.parse(trigger);
                    if (triggerData.closeModal) {
                        const modalEl = document.querySelector('.modal.show');
                        if (modalEl && window.bootstrap) {
                            const modal = window.bootstrap.Modal.getInstance(modalEl);
                            if (modal) {
                                modal.hide();
                            }
                        }
                    }
                } catch (e) {
                    // Do nothing if trigger is not valid JSON
                }
            }
        });
    }

    function showToast(title, message, type = 'info') {
        if (typeof bootstrap === 'undefined') {
            console.warn('Bootstrap not available for toast');
            return;
        }

        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        const toast = createToastElement(title, message, type);
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }

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

    // Helper function for dynamic content loading
    window.loadDynamicContent = function(url, targetId, options = {}) {
        const target = document.getElementById(targetId);
        if (!target) {
            console.error(`Target element not found: ${targetId}`);
            return;
        }

        fetch(url, {
            method: options.method || 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            },
            body: options.body
        })
        .then(response => response.text())
        .then(html => {
            target.innerHTML = html;
            if (options.callback) {
                options.callback(target);
            }
        })
        .catch(error => {
            console.error('Error loading content:', error);
            showToast('Error', 'Failed to load content', 'danger');
        });
    };
})();

/**
 * Form Handling Enhancements
 */
function initFormHandling() {
    // Dynamic form submission
    document.querySelectorAll('[data-ajax-form]').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = form.querySelector('[type="submit"]');
            submitBtn.disabled = true;
            
            try {
                const formData = new FormData(form);
                const response = await window.api.fetch(form.action, {
                    method: form.method,
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.message) {
                        UIUtils.showToast('Success', data.message, 'success');
                    }
                } else {
                    handleFormErrors(form, await response.json());
                }
            } catch (error) {
                UIUtils.showToast('Error', 'An unexpected error occurred', 'danger');
            } finally {
                submitBtn.disabled = false;
            }
        });
    });

    // Real-time input validation
    document.querySelectorAll('[data-validate]').forEach(input => {
        input.addEventListener('input', debounce(() => validateField(input), 300));
    });
}

/**
<<<<<<< HEAD
=======
 * Error Handling System
 */
function initErrorHandling() {
    // Global error handler with duplicate suppression and dev/prod awareness
    let lastErrorMsg = '';
    let lastErrorTime = 0;
    const ERROR_TOAST_SUPPRESS_MS = 10000; // 10 seconds
    const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

    window.onerror = function(message, source, lineno, colno, error) {
        console.error('Global error:', { message, source, lineno, colno, error });
        const now = Date.now();
        const errorMsg = `${message} @ ${source}:${lineno}`;
        if (isDev || (errorMsg !== lastErrorMsg || now - lastErrorTime > ERROR_TOAST_SUPPRESS_MS)) {
            UIUtils.showToast('Application Error', 'An unexpected error occurred', 'danger');
            lastErrorMsg = errorMsg;
            lastErrorTime = now;
        }
        return true;
    };

    window.addEventListener('unhandledrejection', event => {
        console.error('Unhandled rejection:', event.reason);
        if (isDev || (event.reason && event.reason.message !== lastErrorMsg)) {
            UIUtils.showToast('Request Failed', event.reason && event.reason.message ? event.reason.message : 'Action failed', 'danger');
            lastErrorMsg = event.reason && event.reason.message ? event.reason.message : '';
            lastErrorTime = Date.now();
        }
        event.preventDefault();
    });
}

/**
>>>>>>> origin/codex/add-window.showtoast-assignment
 * Analytics Integration
 */
function initAnalytics() {
    // Google Analytics
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag('js', new Date());
    gtag('config', 'G-XXXXXX');

    // Error tracking
    window.addEventListener('error', event => {
        if (window.ga) {
            ga('send', 'exception', {
                exDescription: `${event.message} @ ${event.filename}:${event.lineno}:${event.colno}`,
                exFatal: true
            });
        }
    });
}

/**
 * UI Utilities
 */
<<<<<<< HEAD
=======

/**
 * Security Utilities
 */
>>>>>>> origin/codex/add-window.showtoast-assignment
function sanitizeInput(input) {
    const temp = document.createElement('div');
    temp.textContent = input;
    return temp.innerHTML;
}

/**
 * Performance Optimizations
 */
function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

/**
 * Third-Party Integrations
 */
function loadExternalScript(url, callback) {
    const script = document.createElement('script');
    script.src = url;
    script.async = true;
    script.onload = callback;
    document.head.appendChild(script);
}

/**
 * Application-Specific Customizations
 */
function initCustomHooks() {
    // Dynamic content loading
    document.querySelectorAll('[data-dynamic-content]').forEach(container => {
        const url = container.dataset.dynamicContent;
        if (url) {
            loadDynamicContent(container, url);
        }
    });

    // Table sorting
    document.querySelectorAll('.sortable-table').forEach(table => {
        new Tablesort(table);
    });
}

/**
 * Document Ready Initialization
 */
(function() {
    // Initialize core functionality
    initFormHandling();
    
    // Lazy loading for images
    if ('loading' in HTMLImageElement.prototype) {
        document.querySelectorAll('img[loading="lazy"]').forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        // Polyfill for lazy loading
        loadExternalScript('https://cdn.jsdelivr.net/npm/loading-attribute-polyfill@2.0.1/dist/loading-attribute-polyfill.min.js');
    }

    // Initialize any custom components
    window.App = window.App || {};
    window.App.init = () => {
        console.log('Application initialized');
    };

    // Custom Event Handlers
    document.addEventListener('ajax:success', (event) => {
        const [data, status, xhr] = event.detail;
        showToast('Success', data.message || 'Action completed successfully', 'success');
    });

    document.addEventListener('ajax:error', (event) => {
        const [error, status, xhr] = event.detail;
        showToast('Error', error.message || 'Action failed', 'danger');
    });

    // Note: Modal-related htmx:afterRequest handling has been moved to modal-handler.js
    // to consolidate all modal logic in one place

})();

<<<<<<< HEAD
=======
/**
 * Custom Event Handlers
 */
document.addEventListener('ajax:success', (event) => {
    const [data, status, xhr] = event.detail;
    UIUtils.showToast('Success', data.message || 'Action completed successfully', 'success');
});

document.addEventListener('ajax:error', (event) => {
    const [error, status, xhr] = event.detail;
    UIUtils.showToast('Error', error.message || 'Action failed', 'danger');
});

>>>>>>> origin/codex/add-window.showtoast-assignment
// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    const uiUtils = require('./ui-utils');
    module.exports = {
        debounce,
        showToast: uiUtils.showToast,
        sanitizeInput
    };
}