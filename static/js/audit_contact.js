// audit_contact.js
document.addEventListener('DOMContentLoaded', function() {
  const contactCards = document.querySelectorAll('.contact-card');
  contactCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    card.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 