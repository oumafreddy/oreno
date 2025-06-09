// issueworkingpaper_modal_form.js
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('workingPaperForm');
  if (!form) return;

  // Handle form submission
  form.addEventListener('htmx:beforeRequest', function(event) {
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('wp-upload-spinner');
    const submitText = document.getElementById('submitText');
    if (submitBtn && spinner && submitText) {
      submitBtn.disabled = true;
      spinner.classList.remove('d-none');
      submitText.textContent = 'Saving...';
    }
  });

  // Handle response after form submission
  form.addEventListener('htmx:afterRequest', function(event) {
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('wp-upload-spinner');
    const submitText = document.getElementById('submitText');
    if (submitBtn && spinner && submitText) {
      submitBtn.disabled = false;
      spinner.classList.add('d-none');
      submitText.textContent = 'Save';
    }
    // Handle successful form submission
    if (event.detail.successful) {
      try {
        const data = event.detail.xhr.responseJSON;
        if (data && data.form_is_valid) {
          // Close the modal
          const modal = bootstrap.Modal.getInstance(document.getElementById('mainModal'));
          if (modal) modal.hide();
          // Refresh the working papers list
          if (data.html_list) {
            const container = document.getElementById('workingpapers-list-container');
            if (container) container.innerHTML = data.html_list;
          }
        }
      } catch (e) {
        console.error('Error processing response:', e);
      }
    }
  });
}); 