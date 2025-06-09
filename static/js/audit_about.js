// audit_about.js
document.addEventListener('DOMContentLoaded', function() {
  const aboutCards = document.querySelectorAll('.about-card');
  aboutCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    card.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 