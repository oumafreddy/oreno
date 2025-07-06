/**
 * Engagement Modal Form JavaScript
 * Handles engagement-specific form logic
 * Generic modal functionality is now handled by modal-handler.js
 */

document.addEventListener('DOMContentLoaded', function() {
  // Engagement-specific: Normalize date input values
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