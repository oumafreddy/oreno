// audit_reports.js
document.addEventListener('DOMContentLoaded', function() {
  const reportCards = document.querySelectorAll('.report-card');
  reportCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    card.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 