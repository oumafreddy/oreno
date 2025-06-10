// note_modal_form.js
// Robust modal handler for Note modals, matching Issue modal pattern

document.addEventListener('DOMContentLoaded', function() {
  if (!document.body) return;

  // Show the mainModal when HTMX loads the note form into the modal body
  document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target && evt.detail.target.classList.contains('modal-body')) {
      var modalEl = document.getElementById('mainModal');
      if (modalEl && typeof bootstrap !== 'undefined') {
        var modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
      }
    }
  });

  // Handle form submission (if present)
  document.body.addEventListener('htmx:afterRequest', function(event) {
    // Only close modal if the request was for the note form and was successful
    var form = document.querySelector('#mainModal form');
    if (form && event.detail && event.detail.xhr && event.detail.xhr.responseURL && event.detail.successful) {
      const modalEl = document.getElementById('mainModal');
      if (modalEl && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) {
          modal.hide();
        }
      }
      // Refresh note list
      const noteList = document.getElementById('note-list-container');
      if (noteList) {
        htmx.trigger(noteList, 'refresh');
      }
    }
  });

  // Initialize CKEditor for the note content textarea (if present)
  var contentTextarea = document.getElementById('id_content');
  if (contentTextarea && typeof ClassicEditor !== 'undefined') {
    ClassicEditor
      .create(contentTextarea, {
        toolbar: ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', '|', 'undo', 'redo'],
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