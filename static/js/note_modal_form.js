// note_modal_form.js
(function() {
  var form = document.getElementById('noteForm');
  if (!form) return;
  form.addEventListener('htmx:afterRequest', function(event) {
    try {
      var detail = event.detail;
      if (detail && detail.xhr && detail.xhr.getResponseHeader('content-type') && detail.xhr.getResponseHeader('content-type').includes('application/json')) {
        var data = JSON.parse(detail.xhr.responseText);
        if (data.form_is_valid && data.html_list) {
          var container = document.getElementById('note-list-container');
          if (container) container.innerHTML = data.html_list;
          var modalEl = document.getElementById('globalModal');
          if (modalEl && window.bootstrap) {
            var modal = window.bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
          }
        } else if (data.html_form) {
          var modalBody = document.querySelector('#globalModal .modal-body');
          if (modalBody) modalBody.innerHTML = data.html_form;
        }
      }
    } catch (e) {}
  });
})();

document.addEventListener('DOMContentLoaded', function() {
  var cancelBtn = document.getElementById('note-cancel-btn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', function() {
      var url = cancelBtn.getAttribute('data-engagement-url');
      if (url) window.location.href = url;
    });
  }
}); 