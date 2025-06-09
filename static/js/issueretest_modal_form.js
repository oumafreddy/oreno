// issueretest_modal_form.js
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('issueretestForm');
  if (!form) return;

  // Handle form submission
  form.addEventListener('htmx:beforeRequest', function(event) {
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('retest-upload-spinner');
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
    const spinner = document.getElementById('retest-upload-spinner');
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
          const modal = bootstrap.Modal.getInstance(document.getElementById('globalModal'));
          if (modal) modal.hide();
          
          // Refresh the retests list
          if (data.html_list) {
            const container = document.getElementById('issueretest-list-container');
            if (container) container.innerHTML = data.html_list;
          }
          
          // Show success message
          if (window.showToast) {
            window.showToast(data.message || 'Retest saved successfully!', 'success');
          }
        } else if (data.html_form) {
          // Update form with validation errors
          document.getElementById('modal-body').innerHTML = data.html_form;
        }
      } catch (e) {
        console.error('Error processing response:', e);
        if (window.showToast) {
          window.showToast('An error occurred while saving. Please try again.', 'danger');
        }
      }
    }
  });

  // Add form validation
  form.addEventListener('submit', function(event) {
    if (!form.checkValidity()) {
      event.preventDefault();
      event.stopPropagation();
    }
    form.classList.add('was-validated');
  });
}); 