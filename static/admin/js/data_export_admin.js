// Data Export Admin JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin interface enhancements
    initDataExportAdmin();
});

function initDataExportAdmin() {
    // Add status badges to list view
    addStatusBadges();
    
    // Add export type and format badges
    addTypeBadges();
    
    // Enhance file size display
    enhanceFileSizeDisplay();
    
    // Add action buttons
    addActionButtons();
    
    // Initialize tooltips
    initTooltips();
    
    // Add bulk action confirmations
    addBulkActionConfirmations();
}

function addStatusBadges() {
    // Find status cells and add badges
    const statusCells = document.querySelectorAll('td.field-status');
    
    statusCells.forEach(cell => {
        const status = cell.textContent.trim().toLowerCase();
        const badge = document.createElement('span');
        badge.className = `status-badge status-${status}`;
        badge.textContent = status;
        cell.innerHTML = '';
        cell.appendChild(badge);
    });
}

function addTypeBadges() {
    // Add export type badges
    const typeCells = document.querySelectorAll('td.field-export_type');
    typeCells.forEach(cell => {
        const type = cell.textContent.trim();
        const badge = document.createElement('span');
        badge.className = 'export-type';
        badge.textContent = type;
        cell.innerHTML = '';
        cell.appendChild(badge);
    });
    
    // Add export format badges
    const formatCells = document.querySelectorAll('td.field-export_format');
    formatCells.forEach(cell => {
        const format = cell.textContent.trim();
        const badge = document.createElement('span');
        badge.className = 'export-format';
        badge.textContent = format;
        cell.innerHTML = '';
        cell.appendChild(badge);
    });
}

function enhanceFileSizeDisplay() {
    // Enhance file size display with better formatting
    const sizeCells = document.querySelectorAll('td.field-file_size_display');
    sizeCells.forEach(cell => {
        const size = cell.textContent.trim();
        if (size && size !== 'N/A') {
            cell.className = 'file-size';
        }
    });
    
    // Enhance processing time display
    const timeCells = document.querySelectorAll('td.field-processing_time_display');
    timeCells.forEach(cell => {
        const time = cell.textContent.trim();
        if (time && time !== 'N/A') {
            cell.className = 'processing-time';
        }
    });
}

function addActionButtons() {
    // Add action buttons to each row
    const rows = document.querySelectorAll('#changelist tbody tr');
    
    rows.forEach(row => {
        const actionsCell = row.querySelector('td.field-download_link');
        if (actionsCell) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'action-buttons';
            
            // Get export ID from the row
            const idCell = row.querySelector('td.field-id');
            const exportId = idCell ? idCell.textContent.trim() : null;
            
            if (exportId) {
                // Add view details button
                const viewBtn = createActionButton('View', 'primary', `/admin/admin_module/dataexportlog/${exportId}/change/`);
                actionsDiv.appendChild(viewBtn);
                
                // Add download button if available
                const downloadLink = actionsCell.querySelector('a');
                if (downloadLink) {
                    const downloadBtn = createActionButton('Download', 'success', downloadLink.href);
                    actionsDiv.appendChild(downloadBtn);
                }
                
                // Add delete button
                const deleteBtn = createActionButton('Delete', 'danger', null, 'delete-export', exportId);
                actionsDiv.appendChild(deleteBtn);
            }
            
            actionsCell.innerHTML = '';
            actionsCell.appendChild(actionsDiv);
        }
    });
}

function createActionButton(text, type, href, className = null, dataId = null) {
    const button = document.createElement('a');
    button.className = `action-button ${type}`;
    if (className) button.classList.add(className);
    if (dataId) button.setAttribute('data-export-id', dataId);
    button.textContent = text;
    
    if (href) {
        button.href = href;
    } else if (className === 'delete-export') {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            confirmDelete(dataId);
        });
    }
    
    return button;
}

function confirmDelete(exportId) {
    if (confirm('Are you sure you want to delete this export? This action cannot be undone.')) {
        // Create a form to submit the delete action
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/admin_module/dataexportlog/${exportId}/delete/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

function initTooltips() {
    // Initialize tooltips for better UX
    const tooltipElements = document.querySelectorAll('[title]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this, this.getAttribute('title'));
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'admin-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 1000;
        pointer-events: none;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.bottom + 5) + 'px';
    
    element._tooltip = tooltip;
}

function hideTooltip() {
    const tooltips = document.querySelectorAll('.admin-tooltip');
    tooltips.forEach(tooltip => tooltip.remove());
}

function addBulkActionConfirmations() {
    // Add confirmation for bulk actions
    const actionSelect = document.querySelector('#action');
    if (actionSelect) {
        actionSelect.addEventListener('change', function() {
            const selectedAction = this.value;
            
            if (selectedAction === 'delete_selected_action') {
                if (!confirm('Are you sure you want to delete the selected exports? This action cannot be undone.')) {
                    this.value = '';
                    return false;
                }
            }
            
            if (selectedAction === 'cleanup_expired_action') {
                if (!confirm('Are you sure you want to cleanup expired exports? This will remove expired files.')) {
                    this.value = '';
                    return false;
                }
            }
        });
    }
}

// Export statistics dashboard
function updateExportStats() {
    // This function can be used to update export statistics in real-time
    fetch('/admin-module/data-export/statistics/')
        .then(response => response.json())
        .then(data => {
            // Update statistics display
            updateStatsDisplay(data);
        })
        .catch(error => {
            console.error('Error fetching export statistics:', error);
        });
}

function updateStatsDisplay(stats) {
    // Update statistics display elements
    const elements = {
        'total-exports': stats.total_exports,
        'completed-exports': stats.completed_exports,
        'pending-exports': stats.pending_exports,
        'failed-exports': stats.failed_exports,
        'total-size': stats.total_size_mb
    };
    
    Object.keys(elements).forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            element.textContent = elements[key];
        }
    });
}

// Auto-refresh functionality for pending exports
function startAutoRefresh() {
    // Check if there are pending exports
    const pendingExports = document.querySelectorAll('.status-pending');
    
    if (pendingExports.length > 0) {
        // Refresh the page every 30 seconds if there are pending exports
        setTimeout(() => {
            location.reload();
        }, 30000);
    }
}

// Initialize auto-refresh
if (document.querySelector('.status-pending')) {
    startAutoRefresh();
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + D to go to dashboard
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        window.location.href = '/admin-module/';
    }
    
    // Ctrl/Cmd + N to create new export
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/admin-module/data-export/create/';
    }
});

// Export the functions for use in other scripts
window.DataExportAdmin = {
    initDataExportAdmin,
    addStatusBadges,
    addTypeBadges,
    enhanceFileSizeDisplay,
    addActionButtons,
    confirmDelete,
    updateExportStats,
    startAutoRefresh
};
