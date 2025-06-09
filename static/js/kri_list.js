// kri_list.js
function getKRIFilters() {
    const form = document.getElementById('kri-filter-form');
    const data = new FormData(form);
    const filters = {};
    for (const [k, v] of data.entries()) {
        if (v) filters[k] = v;
    }
    return filters;
}
function updateKRIExportLinks(filters) {
    const params = new URLSearchParams(filters).toString();
    document.getElementById('export-kri-csv').href = '/risk/export/kris/?' + params + '&format=csv';
    document.getElementById('export-kri-excel').href = '/risk/export/kris/?' + params + '&format=excel';
}
function fetchKRIs(page=1) {
    const filters = getKRIFilters();
    filters.page = page;
    fetch('/risk/api/kri-advanced-filter/?' + new URLSearchParams(filters))
        .then(res => res.json())
        .then(data => {
            const tbody = document.querySelector('#kri-table tbody');
            tbody.innerHTML = '';
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
            // Pagination
            const pag = document.getElementById('kri-pagination');
            pag.innerHTML = '';
            for (let i = 1; i <= data.num_pages; i++) {
                pag.innerHTML += `<li class="page-item${i===data.page?' active':''}"><a class="page-link" href="#" onclick="fetchKRIs(${i});return false;">${i}</a></li>`;
            }
            updateKRIExportLinks(filters);
        });
}
document.getElementById('kri-filter-form').addEventListener('submit', function(e) {
    e.preventDefault();
    fetchKRIs(1);
});
document.getElementById('reset-kri-filters').addEventListener('click', function() {
    document.getElementById('kri-filter-form').reset();
    fetchKRIs(1);
});
document.addEventListener('DOMContentLoaded', function() {
    fetchKRIs(1);
}); 