/**
 * Enhanced Public JavaScript for Hashrate Solutions
 * Handles UI interactions, animations, and form submissions with professional polish
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enhanced smooth scrolling with easing
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                const headerHeight = document.querySelector('.public-navbar').offsetHeight;
                const targetPosition = targetElement.offsetTop - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
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

    // Enhanced cookie consent with better UX
    const cookieConsent = document.getElementById('cookieConsent');
    const acceptCookiesBtn = document.getElementById('acceptCookies');
    
    function checkCookieConsent() {
        const cookiesAccepted = document.cookie.split(';').some((item) => item.trim().startsWith('cookies_accepted='));
        
        if (!cookiesAccepted && cookieConsent) {
            setTimeout(() => {
                cookieConsent.classList.add('show');
            }, 1500);
        }
    }
    
    if (acceptCookiesBtn) {
        acceptCookiesBtn.addEventListener('click', function() {
            const d = new Date();
            d.setTime(d.getTime() + (365 * 24 * 60 * 60 * 1000));
            const expires = "expires=" + d.toUTCString();
            document.cookie = "cookies_accepted=true; " + expires + "; path=/";
            
            if (cookieConsent) {
                cookieConsent.classList.remove('show');
            }
        });
    }
    
    checkCookieConsent();

    // Enhanced contact form with validation and better UX
    const contactForm = document.getElementById('contactForm');
    // If ModernWebsite handles forms (dataset.handler === 'modern'), avoid duplicate handling here
    if (contactForm && (typeof ModernWebsite === 'undefined') && contactForm.dataset.handler !== 'modern') {
        const formInputs = contactForm.querySelectorAll('input, textarea');
        
        // Add floating label effect
        formInputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                if (!this.value) {
                    this.parentElement.classList.remove('focused');
                }
            });
            
            // Check if input has value on load
            if (input.value) {
                input.parentElement.classList.add('focused');
            }
        });

        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Basic validation
            let isValid = true;
            const formData = new FormData(contactForm);
            const formObject = {};
            
            formData.forEach((value, key) => {
                formObject[key] = value;
                if (!value.trim()) {
                    isValid = false;
                    const input = contactForm.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.classList.add('error');
                        setTimeout(() => input.classList.remove('error'), 3000);
                    }
                }
            });
            
            if (!isValid) {
                showNotification('Please fill in all required fields.', 'error');
                return;
            }
            
            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(formObject.email)) {
                showNotification('Please enter a valid email address.', 'error');
                return;
            }
            
            // Show loading state
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Sending...';
            submitBtn.disabled = true;
            
            // Delegate to backend if available
            fetch('/contact/submit/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(Object.assign({}, formObject, {
                    company: formData.get('company') || '',
                    form_ts: formData.get('form_ts') || ''
                }))
            }).then(r => r.json()).then(data => {
                if (data && data.success) {
                    showNotification('Thank you for your message! We will get back to you soon.', 'success');
                    contactForm.reset();
                    formInputs.forEach(input => { input.parentElement.classList.remove('focused'); });
                } else {
                    showNotification('Failed to send message. Please try again.', 'error');
                }
            }).catch(() => {
                showNotification('Failed to send message. Please try again.', 'error');
            }).finally(() => {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            });
        });
    }
    
    // Enhanced scroll animations with Intersection Observer
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.service-card, .contact-item, .section-header').forEach(el => {
        observer.observe(el);
    });

    // Enhanced mobile menu with better animations
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuBtn && navMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            navMenu.classList.toggle('show');
            this.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (mobileMenuBtn && navMenu && !mobileMenuBtn.contains(e.target) && !navMenu.contains(e.target)) {
            navMenu.classList.remove('show');
            mobileMenuBtn.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    });
    
    // Enhanced back to top button with smooth animation
    const backToTopButton = document.getElementById('backToTopBtn');
    if (backToTopButton) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
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

    // Add active class to current nav link with smooth transitions
    const navLinks = document.querySelectorAll('.nav-menu a');
    const currentLocation = location.href;
    
    navLinks.forEach(link => {
        if (link.href === currentLocation) {
            link.classList.add('active');
        }
    });

    // Parallax effect for hero section
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            heroSection.style.transform = `translateY(${rate}px)`;
        });
    }

    // Enhanced service card interactions
    document.querySelectorAll('.service-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Typing animation for hero tagline
    const heroTagline = document.querySelector('.hero-tagline');
    if (heroTagline) {
        const text = heroTagline.textContent;
        heroTagline.textContent = '';
        heroTagline.style.opacity = '1';
        
        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                heroTagline.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            }
        };
        
        setTimeout(typeWriter, 1000);
    }
});

// Enhanced notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
    
    // Close button
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    });
}

// Enhanced page load animations
window.addEventListener('load', function() {
    // Trigger hero animations with staggered timing
    const heroElements = [
        { selector: '.hero h1', delay: 300 },
        { selector: '.hero p', delay: 600 },
        { selector: '.hero .btn', delay: 900 }
    ];
    
    heroElements.forEach(({ selector, delay }) => {
        const element = document.querySelector(selector);
        if (element) {
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, delay);
        }
    });
    
    // Animate service cards on load
    document.querySelectorAll('.service-card').forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 1200 + (index * 200));
    });
});

// Enhanced scroll performance
let ticking = false;
function updateOnScroll() {
    // Add any scroll-based animations here
    ticking = false;
}

window.addEventListener('scroll', function() {
    if (!ticking) {
        requestAnimationFrame(updateOnScroll);
        ticking = true;
    }
});

// Helper function to get cookie value by name
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
