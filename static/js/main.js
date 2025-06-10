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

    function initUIComponents() {
        // Check if Bootstrap is available
        if (typeof bootstrap !== 'undefined') {
            // Initialize tooltips
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });

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
                'document.body is null'
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
                        showToast('Success', data.message, 'success');
                    }
                } else {
                    handleFormErrors(form, await response.json());
                }
            } catch (error) {
                showToast('Error', 'An unexpected error occurred', 'danger');
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
})();

/**
 * Custom Event Handlers
 */
document.addEventListener('ajax:success', (event) => {
    const [data, status, xhr] = event.detail;
    showToast('Success', data.message || 'Action completed successfully', 'success');
});

document.addEventListener('ajax:error', (event) => {
    const [error, status, xhr] = event.detail;
    showToast('Error', error.message || 'Action failed', 'danger');
});

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

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        debounce,
        showToast,
        sanitizeInput
    };
}