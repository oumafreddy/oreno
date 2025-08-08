document.addEventListener('DOMContentLoaded', function() {
    function plotOrShowEmpty(containerId, data, layout) {
        const container = document.getElementById(containerId);
        // Debug output (if present)
        const debugEl = document.getElementById(containerId + '-debug');
        if (debugEl) {
            debugEl.textContent = JSON.stringify(data, null, 2);
        }
        if (!container) return;
        // Robust empty check for arrays, objects, and Plotly data
        let isEmpty = false;
        if (!data) {
            isEmpty = true;
        } else if (Array.isArray(data)) {
            isEmpty = data.length === 0 || data.every(
                d => !d || (Array.isArray(d.y) && d.y.every(v => !v)) || (Array.isArray(d.z) && d.z.every(row => row.every(v => !v)))
            );
        } else if (typeof data === 'object') {
            isEmpty = Object.keys(data).length === 0 || Object.values(data).every(v => v === 0 || v === null || v === undefined || (Array.isArray(v) && v.length === 0));
        }
        if (isEmpty) {
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
    // Engagement Status Pie Chart
    const engagementStatus = safeParseJSON('engagement-status-data');
    plotOrShowEmpty('engagement-status-chart', engagementStatus, {
        data: [{
            labels: Object.keys(engagementStatus),
            values: Object.values(engagementStatus),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Issue Risk Pie Chart
    const issueRisk = safeParseJSON('issue-risk-data');
    plotOrShowEmpty('issue-risk-chart', issueRisk, {
        data: [{
            labels: Object.keys(issueRisk),
            values: Object.values(issueRisk),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Approval Status Pie Chart
    const approvalStatus = safeParseJSON('approval-status-data');
    plotOrShowEmpty('approval-status-chart', approvalStatus, {
        data: [{
            labels: Object.keys(approvalStatus),
            values: Object.values(approvalStatus),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });

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
    // Compliance Requirement Framework Pie Chart
    const requirementFramework = safeParseJSON('requirement-framework-data');
    plotOrShowEmpty('framework-dist-chart', requirementFramework, {
        data: [{
            labels: Object.keys(requirementFramework),
            values: Object.values(requirementFramework),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Obligation Overdue/On Time Pie Chart
    const obligationOverdueOntime = safeParseJSON('obligation-overdue-ontime-data');
    plotOrShowEmpty('obligation-overdue-ontime-chart', obligationOverdueOntime, {
        data: [{
            labels: Object.keys(obligationOverdueOntime),
            values: Object.values(obligationOverdueOntime),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Policy Expiry Pie Chart
    const policyExpiry = safeParseJSON('policy-expiry-data');
    plotOrShowEmpty('policy-expiry-chart', policyExpiry, {
        data: [{
            labels: Object.keys(policyExpiry),
            values: Object.values(policyExpiry),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Obligation Owner Workload Bar Chart
    const obligationOwnerWorkload = safeParseJSON('obligation-owner-workload-data');
    plotOrShowEmpty('obligation-owner-workload-chart', obligationOwnerWorkload, {
        data: [{
            x: Object.keys(obligationOwnerWorkload),
            y: Object.values(obligationOwnerWorkload),
            type: 'bar',
            marker: { color: '#2563eb' },
        }],
        options: {height: 250, margin: { t: 0, b: 40, l: 40, r: 0 }, showlegend: false}
    });
    // Contract Status Pie Chart
    const contractStatus = safeParseJSON('contract-status-data');
    plotOrShowEmpty('contract-status-chart', contractStatus, {
        data: [{
            labels: Object.keys(contractStatus),
            values: Object.values(contractStatus),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Contract Type Pie Chart
    const contractType = safeParseJSON('contract-type-data');
    plotOrShowEmpty('contract-type-chart', contractType, {
        data: [{
            labels: Object.keys(contractType),
            values: Object.values(contractType),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Contract Party Pie Chart
    const contractParty = safeParseJSON('contract-party-data');
    plotOrShowEmpty('contract-party-chart', contractParty, {
        data: [{
            labels: Object.keys(contractParty),
            values: Object.values(contractParty),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Milestone Type Pie Chart
    const milestoneType = safeParseJSON('milestone-type-data');
    plotOrShowEmpty('milestone-type-chart', milestoneType, {
        data: [{
            labels: Object.keys(milestoneType),
            values: Object.values(milestoneType),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Milestone Status Pie Chart
    const milestoneStatus = safeParseJSON('milestone-status-data');
    plotOrShowEmpty('milestone-status-chart', milestoneStatus, {
        data: [{
            labels: Object.keys(milestoneStatus),
            values: Object.values(milestoneStatus),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Contract Expiry Pie Chart
    const contractExpiry = safeParseJSON('contract-expiry-data');
    plotOrShowEmpty('contract-expiry-chart', contractExpiry, {
        data: [{
            labels: Object.keys(contractExpiry),
            values: Object.values(contractExpiry),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Case Status Pie Chart
    const caseStatus = safeParseJSON('case-status-data');
    plotOrShowEmpty('case-status-chart', caseStatus, {
        data: [{
            labels: Object.keys(caseStatus),
            values: Object.values(caseStatus),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Task Status Pie Chart
    const taskStatus = safeParseJSON('task-status-data');
    plotOrShowEmpty('task-status-chart', taskStatus, {
        data: [{
            labels: Object.keys(taskStatus),
            values: Object.values(taskStatus),
            type: 'pie',
            textinfo: 'label+percent',
            insidetextorientation: 'radial',
        }],
        options: {height: 250, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
    });
    // Document Management Status Pie Chart
    const statusChart = safeParseJSON('status-chart-data');
    plotOrShowEmpty('statusChart', statusChart, {
        data: [{
            type: 'pie',
            labels: Object.keys(statusChart),
            values: Object.values(statusChart),
            textinfo: 'label+percent',
            hole: .4
        }],
        options: {title: 'Requests by Status'}
    });
    // Uploads Over Time Bar Chart
    const uploadsChart = safeParseJSON('uploads-chart-data');
    plotOrShowEmpty('uploadsChart', uploadsChart, {
        data: [{
            type: 'bar',
            x: Object.keys(uploadsChart),
            y: Object.values(uploadsChart),
            marker: {color: 'rgb(58,200,225)'}
        }],
        options: {title: 'Uploads Over Time', xaxis: {title: 'Date'}, yaxis: {title: 'Uploads'}}
    });
    // Admin Module Role Distribution Pie Chart
    const roleDist = safeParseJSON('role-distribution-data');
    if (Array.isArray(roleDist) && roleDist.length > 0) {
        plotOrShowEmpty('role-pie-chart', roleDist, {
            data: [{
                values: roleDist.map(x => x.count),
                labels: roleDist.map(x => x.role),
                type: 'pie',
                marker: { colors: ['#2563eb', '#f59e42', '#6c757d'] },
                textinfo: 'label+percent',
                insidetextorientation: 'radial',
            }],
            options: {height: 300, margin: { t: 0, b: 0, l: 0, r: 0 }, showlegend: true}
        });
    } else {
        plotOrShowEmpty('role-pie-chart', [], {data: [], options: {}});
    }
    // Defensive checks for dashboard AJAX URLs
    if (typeof window.RISK_API_HEATMAP_URL === 'string' && window.RISK_API_HEATMAP_URL && typeof window.RISK_SELECTED_REGISTER !== 'undefined') {
        fetch(window.RISK_API_HEATMAP_URL + '?register=' + encodeURIComponent(window.RISK_SELECTED_REGISTER))
          .then(response => response.json())
          .then(data => {
              plotOrShowEmpty('risk-heatmap', data.data, data.layout);
              const debugEl = document.getElementById('risk-heatmap-debug');
              if (debugEl) debugEl.textContent = JSON.stringify(data, null, 2);
          })
          .catch(err => {
              const container = document.getElementById('risk-heatmap');
              if (container) container.innerHTML = '<div class="text-danger text-center py-5">Failed to load data</div>';
          });
    } else {
        console.warn('RISK_API_HEATMAP_URL or RISK_SELECTED_REGISTER not set; skipping heatmap fetch.');
    }
    if (typeof window.RISK_API_ASSESSMENT_TIMELINE_URL === 'string' && window.RISK_API_ASSESSMENT_TIMELINE_URL && typeof window.RISK_SELECTED_REGISTER !== 'undefined') {
        fetch(window.RISK_API_ASSESSMENT_TIMELINE_URL + '?register=' + encodeURIComponent(window.RISK_SELECTED_REGISTER))
          .then(response => response.json())
          .then(data => {
              plotOrShowEmpty('assessment-timeline', data.data, data.layout);
              const debugEl = document.getElementById('assessment-timeline-debug');
              if (debugEl) debugEl.textContent = JSON.stringify(data, null, 2);
          })
          .catch(err => {
              const container = document.getElementById('assessment-timeline');
              if (container) container.innerHTML = '<div class="text-danger text-center py-5">Failed to load data</div>';
          });
    } else {
        console.warn('RISK_API_ASSESSMENT_TIMELINE_URL or RISK_SELECTED_REGISTER not set; skipping assessment timeline fetch.');
    }
    // CSP-compliant event handlers for year/month select
    const yearSelect = document.getElementById('year-select');
    const monthSelect = document.getElementById('month-select');
    const periodForm = document.getElementById('period-filter-form');
    if (yearSelect && periodForm) {
        yearSelect.addEventListener('change', function() {
            periodForm.submit();
        });
    }
    if (monthSelect && periodForm) {
        monthSelect.addEventListener('change', function() {
            periodForm.submit();
        });
    }
}); 