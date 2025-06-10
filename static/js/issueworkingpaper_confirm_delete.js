// issueworkingpaper_confirm_delete.js
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('workingPaperDeleteForm');
  if (!form) return;

  // Handle form submission
  form.addEventListener('htmx:beforeRequest', function() {
    const deleteBtn = document.getElementById('deleteBtn');
    const spinner = document.getElementById('delete-spinner');
    const deleteText = document.getElementById('deleteText');
    if (deleteBtn && spinner && deleteText) {
      deleteBtn.disabled = true;
      spinner.classList.remove('d-none');
      deleteText.textContent = 'Deleting...';
    }
  });

  // Handle response after form submission
  form.addEventListener('htmx:afterRequest', function(event) {
    const deleteBtn = document.getElementById('deleteBtn');
    const spinner = document.getElementById('delete-spinner');
    const deleteText = document.getElementById('deleteText');
    if (deleteBtn && spinner && deleteText) {
      deleteBtn.disabled = false;
      spinner.classList.add('d-none');
      deleteText.textContent = 'Delete';
    }
    // Handle successful deletion
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