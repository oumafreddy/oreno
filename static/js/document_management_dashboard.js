// document_management_dashboard.js
// Comprehensive document management dashboard chart rendering and data handling

document.addEventListener('DOMContentLoaded', function() {
    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('document-management-dashboard-vars');
    if (varsEl) {
        window.DOCUMENT_MANAGEMENT_STATUS_URL = varsEl.getAttribute('data-status-url');
        window.DOCUMENT_MANAGEMENT_UPLOADS_URL = varsEl.getAttribute('data-uploads-url');
    }

    // Utility function to safely parse JSON data
    function safeParseJSON(elementId) {
        try {
            const el = document.getElementById(elementId);
            if (!el) return {};
            const text = el.textContent.trim();
            if (!text) return {};
            return JSON.parse(text);
        } catch (e) {
            console.warn('Failed to parse JSON for', elementId, e);
            return {};
        }
    }

    // Utility function to render charts with error handling
    function renderChart(containerId, data, chartType = 'pie', options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn('Container not found:', containerId);
            return;
        }

        // Check if data is empty
        if (!data || Object.keys(data).length === 0 || Object.values(data).every(v => !v)) {
            container.innerHTML = '<div class="text-muted text-center py-5"><i class="bi bi-bar-chart"></i><br>No data available</div>';
            return;
        }

        // Default chart options
        const defaultOptions = {
            height: 250,
            margin: { t: 10, b: 10, l: 10, r: 10 },
            showlegend: true,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)'
        };

        const finalOptions = { ...defaultOptions, ...options };

        let chartData;
        if (chartType === 'pie') {
            chartData = [{
                labels: Object.keys(data),
                values: Object.values(data),
                type: 'pie',
                textinfo: 'label+percent',
                insidetextorientation: 'radial',
                hole: 0.4,
                marker: {
                    colors: ['#2563eb', '#f59e42', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']
                }
            }];
        } else if (chartType === 'bar') {
            chartData = [{
                x: Object.keys(data),
                y: Object.values(data),
                type: 'bar',
                marker: { 
                    color: 'rgb(58,200,225)',
                    line: { color: '#1e40af', width: 1 }
                }
            }];
            finalOptions.margin.b = 40;
            finalOptions.margin.l = 40;
        }

        try {
            Plotly.newPlot(containerId, chartData, finalOptions);
        } catch (error) {
            console.error('Failed to render chart:', containerId, error);
            container.innerHTML = '<div class="text-danger text-center py-5"><i class="bi bi-exclamation-triangle"></i><br>Chart rendering failed</div>';
        }
    }

    // Render all document management dashboard charts
    const statusChartData = safeParseJSON('status-chart-data');
    renderChart('statusChart', statusChartData, 'pie');

    const uploadsChartData = safeParseJSON('uploads-chart-data');
    renderChart('uploadsChart', uploadsChartData, 'bar');

    // Add responsive behavior
    window.addEventListener('resize', function() {
        const charts = ['statusChart', 'uploadsChart'];
        charts.forEach(chartId => {
            const container = document.getElementById(chartId);
            if (container && container.data) {
                Plotly.relayout(chartId, { width: container.offsetWidth });
            }
        });
    });

    // Add click handlers for chart interactions
    document.addEventListener('click', function(e) {
        if (e.target.closest('.card')) {
            const chartContainer = e.target.closest('.card').querySelector('[id$="Chart"]');
            if (chartContainer && chartContainer.data) {
                // Refresh chart on card click for better UX
                Plotly.relayout(chartContainer.id, { autosize: true });
            }
        }
    });

    // Add real-time updates for pending requests
    function updatePendingRequests() {
        const pendingCard = document.querySelector('.card.text-white.bg-warning');
        if (pendingCard) {
            const pendingCount = pendingCard.querySelector('.display-5');
            if (pendingCount && parseInt(pendingCount.textContent) > 0) {
                // Add subtle animation to draw attention to pending requests
                pendingCard.style.animation = 'pulse 2s infinite';
            }
        }
    }

    // Initialize pending requests updates
    updatePendingRequests();
    setInterval(updatePendingRequests, 30000); // Update every 30 seconds

    // Add file upload progress tracking
    function trackFileUploads() {
        const uploadsTable = document.querySelector('table tbody');
        if (uploadsTable) {
            const rows = uploadsTable.querySelectorAll('tr');
            rows.forEach(row => {
                const fileLink = row.querySelector('a[download]');
                if (fileLink) {
                    fileLink.addEventListener('click', function() {
                        // Track file downloads
                        console.log('File downloaded:', this.textContent);
                    });
                }
            });
        }
    }

    // Initialize file upload tracking
    trackFileUploads();
}); 