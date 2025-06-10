// procedureresult_form.js
document.addEventListener('DOMContentLoaded', function() {
  var resultField = document.getElementById('id_result');
  var promptDiv = document.getElementById('procedure-result-prompt');
  if (resultField && promptDiv) {
    function updatePrompt() {
      var value = resultField.value;
      if (value === 'operating_effectively') {
        promptDiv.style.display = 'block';
        promptDiv.className = 'alert alert-success mt-3';
        promptDiv.innerHTML = '<strong>Positive Finding:</strong> Please document any positive findings or best practices identified during this procedure.';
      } else if (value === 'not_effective' || value === 'partially_effective' || value === 'design_ineffective') {
        promptDiv.style.display = 'block';
        promptDiv.className = 'alert alert-warning mt-3';
        promptDiv.innerHTML = '<strong>Issue Required:</strong> This result indicates a control failure. Please ensure an Issue is created and linked to this procedure after saving.';
      } else {
        promptDiv.style.display = 'none';
        promptDiv.innerHTML = '';
      }
    }
    resultField.addEventListener('change', updatePrompt);
    updatePrompt();
  }
}); 