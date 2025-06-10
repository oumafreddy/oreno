// audit_settings.js
document.addEventListener('DOMContentLoaded', function() {
  const settingsCards = document.querySelectorAll('.settings-card');
  settingsCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    card.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 