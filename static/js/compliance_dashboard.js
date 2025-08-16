// compliance_dashboard.js
// Comprehensive compliance dashboard chart rendering and data handling

document.addEventListener('DOMContentLoaded', function() {
    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('compliance-dashboard-vars');
    if (varsEl) {
        window.COMPLIANCE_FRAMEWORK_URL = varsEl.getAttribute('data-framework-url');
        window.COMPLIANCE_OBLIGATION_URL = varsEl.getAttribute('data-obligation-url');
        window.COMPLIANCE_POLICY_EXPIRY_URL = varsEl.getAttribute('data-policy-expiry-url');
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
                    color: '#2563eb',
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

    // Render all compliance dashboard charts
    const requirementFrameworkData = safeParseJSON('requirement-framework-data');
    renderChart('framework-dist-chart', requirementFrameworkData, 'pie');

    const obligationOverdueData = safeParseJSON('obligation-overdue-ontime-data');
    renderChart('obligation-overdue-chart', obligationOverdueData, 'pie');

    const policyExpiryData = safeParseJSON('policy-expiry-data');
    renderChart('policy-expiry-chart', policyExpiryData, 'pie');

    const ownerWorkloadData = safeParseJSON('obligation-owner-workload-data');
    renderChart('owner-workload-chart', ownerWorkloadData, 'bar');

    // Add responsive behavior
    window.addEventListener('resize', function() {
        const charts = ['framework-dist-chart', 'obligation-overdue-chart', 'policy-expiry-chart', 'owner-workload-chart'];
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
            const chartContainer = e.target.closest('.card').querySelector('[id$="-chart"]');
            if (chartContainer && chartContainer.data) {
                // Refresh chart on card click for better UX
                Plotly.relayout(chartContainer.id, { autosize: true });
            }
        }
    });
}); 