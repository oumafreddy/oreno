// engagement_detail.js
document.addEventListener('DOMContentLoaded', function() {
  // Initialize bootstrap modal
  var mainModal = document.getElementById('mainModal');
  var loadingIndicator = document.querySelector('.modal-loading-indicator');

  // Listen for HTMX events
  document.body.addEventListener('htmx:beforeRequest', function(evt) {
    // Show loading indicator when request starts for modal content
    if (evt.detail.target.id === 'modal-body' || evt.detail.target.closest('#modal-body')) {
      if (loadingIndicator) loadingIndicator.classList.remove('d-none');
    }
  });

  document.body.addEventListener('htmx:beforeSwap', function(evt) {
    // Only handle responses for the modal target
    if (evt.detail.target.id === 'modal-body') {
      // Hide loading indicator
      if (loadingIndicator) loadingIndicator.classList.add('d-none');
      // Force the modal to show when content is loaded
      var bsModal = new bootstrap.Modal(mainModal);
      setTimeout(function() {
        bsModal.show();
      }, 50);
    }
  });

  // Close modal when the form is successfully submitted
  document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful && evt.detail.target.closest('#modal-body')) {
      try {
        var contentType = evt.detail.xhr.getResponseHeader('content-type') || '';
        if (contentType.includes('application/json')) {
          var data = JSON.parse(evt.detail.xhr.responseText);
          if (data && data.form_is_valid) {
            var bsModal = bootstrap.Modal.getInstance(mainModal);
            if (bsModal) bsModal.hide();
            // Refresh the current tab content if needed
            var activeTab = document.querySelector('.tab-pane.active');
            if (activeTab && activeTab.id) {
              if (data.html_list) {
                var listContainer = document.getElementById(activeTab.id + '-list-container');
                if (listContainer) listContainer.innerHTML = data.html_list;
              }
            }
          }
        }
        // If not JSON, do nothing: HTMX will swap in the HTML form
      } catch (e) {
        console.error('Error handling modal response:', e);
      }
    }
  });
}); 