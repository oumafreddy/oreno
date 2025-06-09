// public_home.js
document.addEventListener('DOMContentLoaded', function() {
  const features = document.querySelectorAll('.feature');
  features.forEach(feature => {
    feature.addEventListener('mouseenter', function() {
      this.classList.add('shadow-lg');
    });
    feature.addEventListener('mouseleave', function() {
      this.classList.remove('shadow-lg');
    });
  });
}); 