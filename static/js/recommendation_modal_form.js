// recommendation_modal_form.js
(function() {
  // Ensure we have the necessary components
  if (!document.getElementById('recommendationForm')) return;
  // Safely add event listener with proper error handling
  document.getElementById('recommendationForm').addEventListener('htmx:afterRequest', function(event) {
    try {
      var detail = event.detail;
      // Safely check content type to avoid null errors
      var contentType = detail.xhr.getResponseHeader('content-type') || '';
      if (contentType.includes('application/json')) {
        try {
          var data = JSON.parse(detail.xhr.responseText);
          // Handle successful form submission
          if (data.success || data.form_is_valid) {
            // Update the recommendation list if provided
            if (data.html_list) {
              var container = document.getElementById('recommendation-list-container');
              if (container) container.innerHTML = data.html_list;
            }
            // Close the modal safely using OrenoModals if available
            if (window.OrenoModals) {
              window.OrenoModals.hideModal('mainModal');
            } else {
              // Fallback to Bootstrap if OrenoModals not loaded yet
              var modalEl = document.getElementById('mainModal');
              if (modalEl && window.bootstrap && window.bootstrap.Modal) {
                var modal = window.bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
              }
            }
            // Refresh the page content if needed
            if (data.redirect) {
              window.location.href = data.redirect;
            }
          }
        } catch (jsonError) {
          console.warn('Error parsing JSON response', jsonError);
        }
      }
    } catch (e) {
      console.warn('Error handling form response', e);
    }
  });
})(); 