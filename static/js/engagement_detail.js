// engagement_detail.js
// Loading indicator handling for engagement modals
// Modal handling is now centralized in modal-handler.js

document.addEventListener('DOMContentLoaded', function() {
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
    }
  });
}); 