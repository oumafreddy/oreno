/**
 * Public JavaScript for Hashrate Solutions
 * Handles UI interactions, animations, and form submissions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            
            // Don't scroll if it's just a # link
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Adjust for fixed header
                    behavior: 'smooth'
                });
                
                // Update URL without page jump
                if (history.pushState) {
                    history.pushState(null, null, targetId);
                } else {
                    location.hash = targetId;
                }
            }
        });
    });

    // Handle cookie consent
    const cookieConsent = document.getElementById('cookieConsent');
    const acceptCookiesBtn = document.getElementById('acceptCookies');
    
    // Check if user has already accepted cookies
    function checkCookieConsent() {
        const cookiesAccepted = document.cookie.split(';').some((item) => item.trim().startsWith('cookies_accepted='));
        
        if (!cookiesAccepted && cookieConsent) {
            // Show the cookie consent banner after a short delay
            setTimeout(() => {
                cookieConsent.classList.add('show');
            }, 1000);
        }
    }
    
    // Handle accept cookies button click
    if (acceptCookiesBtn) {
        acceptCookiesBtn.addEventListener('click', function() {
            // Set cookie to expire in 365 days
            const d = new Date();
            d.setTime(d.getTime() + (365 * 24 * 60 * 60 * 1000));
            const expires = "expires=" + d.toUTCString();
            document.cookie = "cookies_accepted=true; " + expires + "; path=/";
            
            // Hide the cookie consent banner
            if (cookieConsent) {
                cookieConsent.classList.remove('show');
            }
        });
    }
    
    // Run the cookie consent check
    checkCookieConsent();

    // Handle contact form submission
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(contactForm);
            const formObject = {};
            formData.forEach((value, key) => {
                formObject[key] = value;
            });
            
            // Here you would typically send the form data to your server
            // For now, we'll just show a success message
            alert('Thank you for your message! We will get back to you soon.');
            contactForm.reset();
            
            // In a real implementation, you would use fetch or axios to send the data:
            /*
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // If using Django's CSRF protection
                },
                body: JSON.stringify(formObject)
            })
            .then(response => response.json())
            .then(data => {
                alert('Thank you for your message! We will get back to you soon.');
                contactForm.reset();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('There was an error sending your message. Please try again later.');
            });
            */
        });
    }
    
    // Helper function to get cookie value by name
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    // Add animation on scroll
    const fadeElements = document.querySelectorAll('.fade-in');
    
    const fadeInOnScroll = () => {
        fadeElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementTop < windowHeight - 100) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    };
    
    // Initial check
    fadeInOnScroll();
    
    // Check on scroll
    window.addEventListener('scroll', fadeInOnScroll);
    
    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuBtn && navMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            navMenu.classList.toggle('show');
            this.classList.toggle('active');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (mobileMenuBtn && navMenu && !mobileMenuBtn.contains(e.target) && !navMenu.contains(e.target)) {
            navMenu.classList.remove('show');
            mobileMenuBtn.classList.remove('active');
        }
    });
    
    // Back to Top Button
    const backToTopButton = document.getElementById('backToTopBtn');

    if (backToTopButton) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) { // Show button after scrolling 300px
                backToTopButton.classList.add('visible');
            } else {
                backToTopButton.classList.remove('visible');
            }
        });

        backToTopButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Add active class to current nav link
    const navLinks = document.querySelectorAll('.nav-menu a');
    const currentLocation = location.href;
    
    navLinks.forEach(link => {
        if (link.href === currentLocation) {
            link.classList.add('active');
        }
    });
});

// Initialize animations when the page loads
window.addEventListener('load', function() {
    // Trigger hero animations
    const heroHeading = document.querySelector('.hero h2');
    const heroText = document.querySelector('.hero p');
    const heroButtons = document.querySelectorAll('.hero .btn');
    
    if (heroHeading) {
        setTimeout(() => {
            heroHeading.style.opacity = '1';
            heroHeading.style.transform = 'translateY(0)';
        }, 300);
    }
    
    if (heroText) {
        setTimeout(() => {
            heroText.style.opacity = '1';
            heroText.style.transform = 'translateY(0)';
        }, 500);
    }
    
    if (heroButtons.length > 0) {
        heroButtons.forEach((btn, index) => {
            setTimeout(() => {
                btn.style.opacity = '1';
                btn.style.transform = 'translateY(0)';
            }, 700 + (index * 200));
        });
    }
});
