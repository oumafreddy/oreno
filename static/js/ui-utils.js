(function(window) {
    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
        return container;
    }

    function showToast(title, message, variant = 'success') {
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${variant} border-0`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong>${message ? `<br>${message}` : ''}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        toastContainer.appendChild(toast);
        new bootstrap.Toast(toast, { autohide: true, delay: 5000 }).show();
    }

    function initTooltips(container = document) {
        const tooltipElements = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipElements.forEach(el => new bootstrap.Tooltip(el));
    }

    window.UIUtils = {
        createToastContainer,
        showToast,
        initTooltips
    };
    window.showToast = showToast;
})(window);
