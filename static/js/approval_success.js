// approval_success.js
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    var modalElement = document.querySelector('.modal');
    if (modalElement) {
      var modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
      modal.hide();
    }
    // Read the redirect URL from the data attribute
    var redirectDataElement = document.getElementById('success-redirect-data');
    var redirectUrlValue = null;
    if (redirectDataElement) {
      redirectUrlValue = redirectDataElement.getAttribute('data-redirect-url');
    }
    // If we have a valid redirect URL, navigate to it
    if (redirectUrlValue && redirectUrlValue.length > 0) {
      window.location.href = redirectUrlValue;
    }
  }, 1500);
}); 