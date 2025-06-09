// audit_terms.js
document.addEventListener('DOMContentLoaded', function() {
  const termsCards = document.querySelectorAll('.terms-card');
  termsCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    card.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 