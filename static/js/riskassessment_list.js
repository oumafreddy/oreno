// riskassessment_list.js
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie('csrftoken');

function getAssessmentFilters() {
  const form = document.getElementById('assessment-filter-form');
  const data = new FormData(form);
  const filters = {};
  for (const [k, v] of data.entries()) {
    if (v) filters[k] = v;
  }
  return filters;
}

function updateExportLinks(filters) {
  const params = new URLSearchParams(filters).toString();
  document.getElementById('export-csv').href = '/risk/export/assessments/?' + params + '&format=csv';
  document.getElementById('export-excel').href = '/risk/export/assessments/?' + params + '&format=excel';
}

function showLoading(show) {
  document.getElementById('assessment-loading').style.display = show ? '' : 'none';
}

function showError(msg) {
  const err = document.getElementById('assessment-error');
  err.style.display = msg ? '' : 'none';
  err.textContent = msg || '';
}

function fetchAssessments(page=1) {
  showLoading(true);
  showError('');
  const filters = getAssessmentFilters();
  filters.page = page;
  fetch('/risk/api/assessment-advanced-filter/?' + new URLSearchParams(filters), {
    headers: {'X-CSRFToken': csrftoken, 'Accept': 'application/json'},
    credentials: 'include'
  })
    .then(res => {
      if (!res.ok) throw new Error('Failed to fetch assessments. Please refresh or try again.');
      return res.json();
    })
    .then(data => {
      const tbody = document.querySelector('#assessment-table tbody');
      tbody.innerHTML = '';
      if (!data.results || !Array.isArray(data.results) || data.results.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No assessments found.</td></tr>`;
      } else {
        data.results.forEach(assessment => {
          tbody.innerHTML += `<tr>
            <td><a href="/risk/assessments/${assessment.id}/">${assessment.assessment_name || ''}</a></td>
            <td>${assessment.assessor || ''}</td>
            <td>${assessment.risk ? `<a href="/risk/risks/${assessment.risk.id}/">${assessment.risk.risk_name || ''}</a>` : ''}</td>
            <td>
              <span class="badge ${
                assessment.status === 'draft' ? 'bg-secondary' :
                assessment.status === 'in-progress' ? 'bg-warning' :
                assessment.status === 'completed' ? 'bg-success' : 'bg-info'
              }">${assessment.status ? assessment.status.charAt(0).toUpperCase() + assessment.status.slice(1) : ''}</span>
            </td>
            <td>${assessment.assessment_date || ''}</td>
            <td>
              <a href="/risk/assessments/${assessment.id}/" class="btn btn-sm btn-outline-info" title="View"><i class="bi bi-eye"></i></a>
              <a href="/risk/assessments/${assessment.id}/update/" class="btn btn-sm btn-outline-secondary" title="Edit"><i class="bi bi-pencil"></i></a>
              <a href="/risk/assessments/${assessment.id}/delete/" class="btn btn-sm btn-outline-danger" title="Delete"><i class="bi bi-trash"></i></a>
            </td>
          </tr>`;
        });
      }
      // Pagination
      const pag = document.getElementById('assessment-pagination');
      pag.innerHTML = '';
      if (data.num_pages && data.num_pages > 1) {
        for (let i = 1; i <= data.num_pages; i++) {
          pag.innerHTML += `<li class="page-item${i===data.page?' active':''}"><a class="page-link" href="#" onclick="fetchAssessments(${i});return false;">${i}</a></li>`;
        }
      }
      updateExportLinks(filters);
    })
    .catch(err => {
      showError(err.message);
    })
    .finally(() => {
      showLoading(false);
    });
}

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('assessment-filter-form').addEventListener('submit', function(e) {
    e.preventDefault();
    fetchAssessments(1);
  });
  document.getElementById('reset-filters').addEventListener('click', function() {
    document.getElementById('assessment-filter-form').reset();
    fetchAssessments(1);
  });
  fetchAssessments(1);
}); 