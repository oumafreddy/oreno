// kri_list.js
function getKRIFilters() {
    const form = document.getElementById('kri-filter-form');
    if (!form) return {};
    const data = new FormData(form);
    const filters = {};
    for (const [k, v] of data.entries()) {
        if (v) filters[k] = v;
    }
    return filters;
}
function updateKRIExportLinks(filters) {
    const params = new URLSearchParams(filters).toString();
    const csvLink = document.getElementById('export-kri-csv');
    const excelLink = document.getElementById('export-kri-excel');
    if (csvLink) csvLink.href = '/risk/export/kris/?' + params + '&format=csv';
    if (excelLink) excelLink.href = '/risk/export/kris/?' + params + '&format=excel';
}
function fetchKRIs(page=1) {
    const filters = getKRIFilters();
    filters.page = page;
    fetch('/risk/api/kri-advanced-filter/?' + new URLSearchParams(filters))
        .then(res => res.json())
        .then(data => {
            const tbody = document.querySelector('#kri-table tbody');
            if (tbody) {
            tbody.innerHTML = '';
                if (data.results && Array.isArray(data.results)) {
            data.results.forEach(kri => {
                tbody.innerHTML += `<tr>
                    <td>${kri.name}</td>
                    <td>${kri.risk_name || ''}</td>
                    <td>${kri.value}</td>
                    <td>${kri.unit || ''}</td>
                    <td><span class="badge bg-${kri.status}">${kri.status.charAt(0).toUpperCase() + kri.status.slice(1)}</span></td>
                    <td>${kri.timestamp || ''}</td>
                    <td>
                        <a href="/risk/kri/${kri.id}/" class="btn btn-sm btn-outline-info"><i class="bi bi-eye"></i></a>
                        <a href="/risk/kri/${kri.id}/update/" class="btn btn-sm btn-outline-secondary"><i class="bi bi-pencil"></i></a>
                        <a href="/risk/kri/${kri.id}/delete/" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></a>
                    </td>
                </tr>`;
            });
                }
            }
            // Pagination
            const pag = document.getElementById('kri-pagination');
            if (pag) {
            pag.innerHTML = '';
                if (data.num_pages) {
            for (let i = 1; i <= data.num_pages; i++) {
                pag.innerHTML += `<li class="page-item${i===data.page?' active':''}"><a class="page-link" href="#" onclick="fetchKRIs(${i});return false;">${i}</a></li>`;
                    }
                }
            }
            updateKRIExportLinks(filters);
        })
        .catch(error => {
            console.error('Error fetching KRIs:', error);
        });
}
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('kri-filter-form');
    const resetBtn = document.getElementById('reset-kri-filters');
    
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
    e.preventDefault();
    fetchKRIs(1);
});
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            const form = document.getElementById('kri-filter-form');
            if (form) {
                form.reset();
    fetchKRIs(1);
            }
});
    }
    
    fetchKRIs(1);
}); 