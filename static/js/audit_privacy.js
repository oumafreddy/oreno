// audit_privacy.js
document.addEventListener('DOMContentLoaded', function() {
  const privacyCards = document.querySelectorAll('.privacy-card');
  privacyCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    card.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 