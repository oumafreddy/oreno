// static/js/main.js
/**
 * Core Application Initialization
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initCSRFHandling();
    initUIComponents();
    initAnalytics();
    initErrorHandling();
    initCustomHooks();
});

/**
 * CSRF Token Handling for AJAX Requests
 */
function initCSRFHandling() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Set up AJAX defaults
    $.ajaxSetup({
        headers: { 'X-CSRFToken': csrfToken }
    });

    // Fetch API CSRF handling
    const fetchWithCSRF = (url, options = {}) => {
        options.headers = options.headers || {};
        options.headers['X-CSRFToken'] = csrfToken;
        return fetch(url, options);
    };
    
    window.api = { fetch: fetchWithCSRF };
}

/**
 * UI Components Initialization
 */
function initUIComponents() {
    // Bootstrap component initialization
    const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));

    const popovers = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popovers.forEach(popover => new bootstrap.Popover(popover));

    // Mobile menu toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    const mainNav = document.querySelector('#mainNav');
    
    if (navbarToggler && mainNav) {
        navbarToggler.addEventListener('click', () => {
            mainNav.classList.toggle('show');
        });
    }

    // Dynamic modal handling
    document.querySelectorAll('[data-modal-target]').forEach(trigger => {
        trigger.addEventListener('click', () => {
            const targetModal = document.querySelector(trigger.dataset.modalTarget);
            if (targetModal) {
                const modal = new bootstrap.Modal(targetModal);
                modal.show();
            }
        });
    });

    // Auto-dismiss alerts
    document.querySelectorAll('.alert-auto-dismiss').forEach(alert => {
        setTimeout(() => {
            new bootstrap.Alert(alert).close();
        }, 5000);
    });
}

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
 * Error Handling System
 */
function initErrorHandling() {
    // Global error handler
    window.onerror = function(message, source, lineno, colno, error) {
        console.error('Global error:', { message, source, lineno, colno, error });
        showToast('Application Error', 'A unexpected error occurred', 'danger');
        return true;
    };

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', event => {
        console.error('Unhandled rejection:', event.reason);
        showToast('Request Failed', event.reason.message || 'Action failed', 'danger');
        event.preventDefault();
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
function showToast(title, message, variant = 'success') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    
    toast.className = `toast align-items-center text-bg-${variant} border-0`;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    new bootstrap.Toast(toast, { autohide: true, delay: 5000 }).show();
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

/**
 * Security Utilities
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
        loadDynamicContent(container, url);
    });

    // Table sorting
    document.querySelectorAll('.sortable-table').forEach(table => {
        new Tablesort(table);
    });
}

async function loadDynamicContent(container, url) {
    try {
        const response = await fetch(url);
        if (response.ok) {
            container.innerHTML = await response.text();
            initUIComponents(); // Reinitialize components
        }
    } catch (error) {
        console.error('Content load failed:', error);
    }
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

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        debounce,
        showToast,
        sanitizeInput
    };
}