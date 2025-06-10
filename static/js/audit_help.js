// audit_help.js
document.addEventListener('DOMContentLoaded', function() {
  const helpCards = document.querySelectorAll('.help-card');
  helpCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    card.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 