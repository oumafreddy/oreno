// note_modal_form.js
// CKEditor initialization for Note modals
// Modal handling is now centralized in modal-handler.js

document.addEventListener('DOMContentLoaded', function() {
  if (!document.body) return;

  // Initialize CKEditor for the note content textarea (if present)
  var contentTextarea = document.getElementById('id_content');
  if (contentTextarea && typeof ClassicEditor !== 'undefined') {
    ClassicEditor
      .create(contentTextarea, {
        // Let Django handle the configuration via CKEDITOR_5_CONFIGS
        // This ensures consistency between server-side and client-side
        placeholder: 'Enter your note content here...'
      })
      .then(editor => {
        window.noteEditor = editor;
        // Update textarea with CKEditor content on form submit
        var form = document.querySelector('#mainModal form');
        if (form) {
          form.addEventListener('submit', function(e) {
            editor.updateSourceElement();
          });
        }
      })
      .catch(error => {
        console.error('Error initializing CKEditor:', error);
        var form = document.querySelector('#mainModal form');
        if (form) {
          const errorDiv = document.createElement('div');
          errorDiv.className = 'alert alert-danger';
          errorDiv.textContent = 'Error initializing editor. Please try again.';
          form.insertBefore(errorDiv, form.firstChild);
        }
      });
  } else if (contentTextarea) {
    console.error('CKEditor not loaded');
  }
});

// Handle cancel button (if present)
const cancelBtn = document.getElementById('note-cancel-btn');
if (cancelBtn) {
  cancelBtn.addEventListener('click', function() {
    const url = cancelBtn.getAttribute('data-engagement-url');
    if (url) {
      window.location.href = url;
    }
  });
} 