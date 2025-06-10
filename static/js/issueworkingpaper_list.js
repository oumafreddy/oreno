// issueworkingpaper_list.js

document.addEventListener('DOMContentLoaded', function() {
  if (typeof bootstrap === 'undefined') {
    console.error('Bootstrap JS is not loaded. Please ensure bootstrap.bundle.min.js is loaded before this script.');
    return;
  }

  // Add tooltips to action buttons
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Handle file download errors
  document.querySelectorAll('a[download]').forEach(function(link) {
    link.addEventListener('click', function(e) {
      var href = this.getAttribute('href');
      if (!href) {
        e.preventDefault();
        if (window.showToast) {
          window.showToast('File not found or access denied', 'danger');
        }
      }
    });
  });

  // Add confirmation for delete action
  document.querySelectorAll('[hx-get*="delete"]').forEach(function(button) {
    button.addEventListener('click', function(e) {
      if (!confirm('Are you sure you want to delete this working paper?')) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });

  // Initialize Bootstrap tooltips for data-bs-toggle
  var tooltipTriggerList2 = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList2.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize HTMX logging
  if (window.htmx && typeof htmx.logAll === 'function') {
    htmx.logAll();
  }

  // Handle modal events
  document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'modal-content') {
      var modal = new bootstrap.Modal(document.getElementById('modal'));
      modal.show();
    }
  });

  // Handle form submissions
  document.body.addEventListener('htmx:beforeRequest', function(evt) {
    if (evt.detail.elt.tagName === 'FORM') {
      var submitButton = evt.detail.elt.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
      }
    }
  });

  // Handle successful form submissions
  document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.elt.tagName === 'FORM') {
      var submitButton = evt.detail.elt.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Submit';
      }
    }
  });
}); 