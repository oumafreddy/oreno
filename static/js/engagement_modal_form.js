// engagement_modal_form.js
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('input[type="date"]').forEach(function(input) {
    if (input.value) {
      const dateValue = new Date(input.value);
      if (!isNaN(dateValue.getTime())) {
        const formattedDate = dateValue.toISOString().split('T')[0];
        input.value = formattedDate;
      }
    }
  });
}); 