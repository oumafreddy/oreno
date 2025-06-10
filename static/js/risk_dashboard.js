// risk_dashboard.js
// All page-specific JS for the risk dashboard should go here.
// This file is CSP-compliant and ready for future enhancements.

document.addEventListener('DOMContentLoaded', function() {
    // Example: Add event listeners for register select if needed
    const registerSelect = document.getElementById('register-select');
    const registerForm = document.getElementById('register-filter-form');
    if (registerSelect && registerForm) {
        registerSelect.addEventListener('change', function() {
            registerForm.submit();
        });
    }
    // Add more risk dashboard logic here as needed

    // Set AJAX variables from data attributes (CSP-compliant)
    const varsEl = document.getElementById('risk-dashboard-vars');
    if (varsEl) {
        window.RISK_API_HEATMAP_URL = varsEl.getAttribute('data-heatmap-url');
        window.RISK_API_ASSESSMENT_TIMELINE_URL = varsEl.getAttribute('data-assessment-timeline-url');
        window.RISK_SELECTED_REGISTER = varsEl.getAttribute('data-selected-register');
    }
});

window.RISK_API_HEATMAP_URL = document.getElementById('risk-dashboard-vars')?.dataset.heatmapUrl;
window.RISK_API_ASSESSMENT_TIMELINE_URL = document.getElementById('risk-dashboard-vars')?.dataset.assessmentTimelineUrl;
window.RISK_SELECTED_REGISTER = document.getElementById('risk-dashboard-vars')?.dataset.selectedRegister;

function plotOrShowEmpty(containerId, data, layout) {
    const container = document.getElementById(containerId);
    if (!container) return;
    if (!data || (Array.isArray(data) ? data.length === 0 : Object.keys(data).length === 0)) {
        container.innerHTML = '<div class="text-muted text-center py-5">No data available</div>';
    } else {
        Plotly.newPlot(containerId, layout.data, layout.options);
    }
}
function safeParseJSON(elementId) {
    try {
        const el = document.getElementById(elementId);
        if (!el) return {};
        const text = el.textContent.trim();
        if (!text) return {};
        return JSON.parse(text);
    } catch (e) {
        return {};
    }
}
// Heatmap AJAX placeholder
if (window.RISK_API_HEATMAP_URL && window.RISK_SELECTED_REGISTER) {
    fetch(window.RISK_API_HEATMAP_URL + '?register=' + window.RISK_SELECTED_REGISTER)
        .then(response => response.json())
        .then(data => {
            plotOrShowEmpty('risk-heatmap', data, data.layout);
        });
}
// Assessment Timeline AJAX placeholder
if (window.RISK_API_ASSESSMENT_TIMELINE_URL && window.RISK_SELECTED_REGISTER) {
    fetch(window.RISK_API_ASSESSMENT_TIMELINE_URL + '?register=' + window.RISK_SELECTED_REGISTER)
        .then(response => response.json())
        .then(data => {
            plotOrShowEmpty('assessment-timeline', data, data.layout);
        });
}
// Register selector auto-submit
const regSelect = document.getElementById('register-select');
if (regSelect) {
    regSelect.addEventListener('change', function() {
        this.form.submit();
    });
}
// Risk Category Pie Chart
const riskCategory = safeParseJSON('risk-category-data');
plotOrShowEmpty('risk-category-chart', riskCategory, {
    data: [{
        labels: Object.keys(riskCategory),
        values: Object.values(riskCategory),
        type: 'pie',
        textinfo: 'label+percent',
        insidetextorientation: 'radial',
    }],
    options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
});
// Risk Status Pie Chart
const riskStatus = safeParseJSON('risk-status-data');
plotOrShowEmpty('risk-status-chart', riskStatus, {
    data: [{
        labels: Object.keys(riskStatus),
        values: Object.values(riskStatus),
        type: 'pie',
        textinfo: 'label+percent',
        insidetextorientation: 'radial',
    }],
    options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
});
// Risk Owner Pie Chart
const riskOwner = safeParseJSON('risk-owner-data');
plotOrShowEmpty('risk-owner-chart', riskOwner, {
    data: [{
        labels: Object.keys(riskOwner),
        values: Object.values(riskOwner),
        type: 'pie',
        textinfo: 'label+percent',
        insidetextorientation: 'radial',
    }],
    options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
});
// Risk Register Pie Chart
const riskRegister = safeParseJSON('risk-register-data');
plotOrShowEmpty('risk-register-chart', riskRegister, {
    data: [{
        labels: Object.keys(riskRegister),
        values: Object.values(riskRegister),
        type: 'pie',
        textinfo: 'label+percent',
        insidetextorientation: 'radial',
    }],
    options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
});
// KRI Status Pie Chart
const kriStatus = safeParseJSON('kri-status-data');
plotOrShowEmpty('kri-status-chart', kriStatus, {
    data: [{
        labels: Object.keys(kriStatus),
        values: Object.values(kriStatus),
        type: 'pie',
        textinfo: 'label+percent',
        insidetextorientation: 'radial',
    }],
    options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
});
// Control Effectiveness Pie Chart
const controlEffectiveness = safeParseJSON('control-effectiveness-data');
plotOrShowEmpty('control-effectiveness-chart', controlEffectiveness, {
    data: [{
        labels: Object.keys(controlEffectiveness),
        values: Object.values(controlEffectiveness),
        type: 'pie',
        textinfo: 'label+percent',
        insidetextorientation: 'radial',
    }],
    options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
});
// Risk Trend Line Chart
const riskTrend = safeParseJSON('risk-trend-data');
plotOrShowEmpty('risk-trend-chart', riskTrend, {
    data: [{
        x: riskTrend.map(r => r.month),
        y: riskTrend.map(r => r.count),
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Risks Identified'
    }],
    options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: false}
}); 