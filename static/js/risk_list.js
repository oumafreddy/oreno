// risk_list.js
function getRiskFilters() {
    const form = document.getElementById('risk-filter-form');
    if (!form) return {};
    const data = new FormData(form);
    const filters = {};
    for (const [k, v] of data.entries()) {
        if (v) filters[k] = v;
    }
    return filters;
}
function updateRiskExportLinks(filters) {
    const params = new URLSearchParams(filters).toString();
    const csvLink = document.getElementById('export-csv');
    const excelLink = document.getElementById('export-excel');
    if (csvLink) csvLink.href = '/risk/export/risks/?' + params + '&format=csv';
    if (excelLink) excelLink.href = '/risk/export/risks/?' + params + '&format=excel';
}
function showRiskLoading(show) {
    const loadingEl = document.getElementById('risk-loading');
    if (loadingEl) loadingEl.style.display = show ? '' : 'none';
}
function showRiskError(msg) {
    const err = document.getElementById('risk-error');
    if (err) {
        err.style.display = msg ? '' : 'none';
        err.textContent = msg || '';
    }
}
function fetchRisks(page=1) {
    showRiskLoading(true);
    showRiskError('');
    const filters = getRiskFilters();
    filters.page = page;
    fetch('/risk/api/risk-advanced-filter/?' + new URLSearchParams(filters), {
        headers: {'Accept': 'application/json'},
        credentials: 'include'
    })
        .then(res => {
            if (!res.ok) throw new Error('Failed to fetch risks. Please refresh or try again.');
            return res.json();
        })
        .then(data => {
            const tbody = document.querySelector('#risk-table tbody');
            if (tbody) {
                tbody.innerHTML = '';
                if (!data.results || !Array.isArray(data.results) || data.results.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No risks found.</td></tr>`;
                } else {
                    data.results.forEach(risk => {
                        tbody.innerHTML += `<tr>
                            <td><a href="/risk/risks/${risk.id}/">${risk.risk_name || ''}</a></td>
                            <td>${risk.risk_owner || ''}</td>
                            <td>${risk.category || ''}</td>
                            <td>${risk.status || ''}</td>
                            <td>${risk.residual_risk_score || ''}</td>
                            <td>
                                <a href="/risk/risks/${risk.id}/" class="btn btn-sm btn-outline-info" title="View"><i class="bi bi-eye"></i></a>
                                <a href="/risk/risks/${risk.id}/update/" class="btn btn-sm btn-outline-secondary" title="Edit"><i class="bi bi-pencil"></i></a>
                                <a href="/risk/risks/${risk.id}/delete/" class="btn btn-sm btn-outline-danger" title="Delete"><i class="bi bi-trash"></i></a>
                            </td>
                        </tr>`;
                    });
                }
            }
            // Pagination
            const pag = document.getElementById('risk-pagination');
            if (pag) {
                pag.innerHTML = '';
                if (data.num_pages && data.num_pages > 1) {
                    for (let i = 1; i <= data.num_pages; i++) {
                        pag.innerHTML += `<li class="page-item${i===data.page?' active':''}"><a class="page-link" href="#" onclick="fetchRisks(${i});return false;">${i}</a></li>`;
                    }
                }
            }
            updateRiskExportLinks(filters);
        })
        .catch(err => {
            showRiskError(err.message);
        })
        .finally(() => {
            showRiskLoading(false);
        });
}
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('risk-filter-form');
    const resetBtn = document.getElementById('reset-filters');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            fetchRisks(1);
        });
    }
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            const form = document.getElementById('risk-filter-form');
            if (form) {
                form.reset();
                fetchRisks(1);
            }
        });
    }
    fetchRisks(1);
}); 