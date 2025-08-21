/**
 * Password Strength Meter
 * Provides real-time feedback on password strength with visual indicators
 */

class PasswordStrengthMeter {
    constructor(passwordField, meterContainer, options = {}) {
        this.passwordField = passwordField;
        this.meterContainer = meterContainer;
        this.options = {
            minLength: 12,
            showFeedback: true,
            showScore: true,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createMeter();
        this.bindEvents();
        this.updateMeter('');
    }
    
    createMeter() {
        this.meterContainer.innerHTML = `
            <div class="password-strength-container">
                <div class="progress mb-2" style="height: 8px;">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
                <div class="password-strength-info">
                    <small class="strength-text text-muted">Enter a password</small>
                    ${this.options.showScore ? '<small class="strength-score text-muted ms-2"></small>' : ''}
                </div>
                ${this.options.showFeedback ? '<div class="password-feedback mt-2"></div>' : ''}
            </div>
        `;
        
        this.progressBar = this.meterContainer.querySelector('.progress-bar');
        this.strengthText = this.meterContainer.querySelector('.strength-text');
        this.strengthScore = this.meterContainer.querySelector('.strength-score');
        this.feedbackContainer = this.meterContainer.querySelector('.password-feedback');
    }
    
    bindEvents() {
        this.passwordField.addEventListener('input', (e) => {
            this.updateMeter(e.target.value);
        });
        
        this.passwordField.addEventListener('focus', () => {
            this.meterContainer.style.display = 'block';
        });
        
        this.passwordField.addEventListener('blur', () => {
            if (!this.passwordField.value) {
                this.meterContainer.style.display = 'none';
            }
        });
    }
    
    updateMeter(password) {
        const result = this.calculateStrength(password);
        this.updateVisual(result);
        this.updateFeedback(result);
    }
    
    calculateStrength(password) {
        let score = 0;
        const feedback = [];
        
        // Length contribution (up to 25 points)
        if (password.length >= 16) {
            score += 25;
        } else if (password.length >= 12) {
            score += 20;
        } else if (password.length >= 8) {
            score += 15;
        } else if (password.length >= 6) {
            score += 10;
        } else if (password.length > 0) {
            feedback.push('Password is too short');
        }
        
        // Character variety contribution (up to 25 points)
        let charTypes = 0;
        if (/[A-Z]/.test(password)) charTypes++;
        if (/[a-z]/.test(password)) charTypes++;
        if (/[0-9]/.test(password)) charTypes++;
        if (/[^A-Za-z0-9]/.test(password)) charTypes++;
        
        score += charTypes * 6.25; // 25 points / 4 types
        
        if (charTypes < 3 && password.length > 0) {
            feedback.push('Use more character types (uppercase, lowercase, numbers, symbols)');
        }
        
        // Complexity contribution (up to 25 points)
        if (!/(.)\1{2,}/.test(password)) {
            score += 10;
        } else {
            feedback.push('Avoid repeated characters');
        }
        
        if (!/(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)/i.test(password)) {
            score += 10;
        } else {
            feedback.push('Avoid sequential characters');
        }
        
        // Entropy contribution (up to 25 points)
        const uniqueChars = new Set(password).size;
        if (uniqueChars >= 12) {
            score += 25;
        } else if (uniqueChars >= 10) {
            score += 20;
        } else if (uniqueChars >= 8) {
            score += 15;
        } else if (uniqueChars >= 6) {
            score += 10;
        } else if (password.length > 0) {
            feedback.push('Use more unique characters');
        }
        
        // Determine strength level
        let strength = 'Very Weak';
        let strengthClass = 'danger';
        
        if (score >= 80) {
            strength = 'Very Strong';
            strengthClass = 'success';
        } else if (score >= 60) {
            strength = 'Strong';
            strengthClass = 'info';
        } else if (score >= 40) {
            strength = 'Moderate';
            strengthClass = 'warning';
        } else if (score >= 20) {
            strength = 'Weak';
            strengthClass = 'danger';
        }
        
        return {
            score: Math.min(100, Math.round(score)),
            strength: strength,
            strengthClass: strengthClass,
            feedback: feedback,
            charTypes: charTypes,
            length: password.length,
            uniqueChars: uniqueChars
        };
    }
    
    updateVisual(result) {
        // Update progress bar
        this.progressBar.style.width = `${result.score}%`;
        this.progressBar.className = `progress-bar bg-${result.strengthClass}`;
        
        // Update strength text
        this.strengthText.textContent = result.strength;
        this.strengthText.className = `strength-text text-${result.strengthClass}`;
        
        // Update score if enabled
        if (this.strengthScore) {
            this.strengthScore.textContent = `${result.score}/100`;
            this.strengthScore.className = `strength-score text-${result.strengthClass} ms-2`;
        }
    }
    
    updateFeedback(result) {
        if (!this.feedbackContainer) return;
        
        if (result.feedback.length === 0) {
            this.feedbackContainer.innerHTML = '<small class="text-success">✓ Password meets requirements</small>';
        } else {
            this.feedbackContainer.innerHTML = result.feedback.map(feedback => 
                `<small class="text-danger d-block">• ${feedback}</small>`
            ).join('');
        }
    }
}

// Auto-initialize password strength meters
document.addEventListener('DOMContentLoaded', function() {
    const passwordFields = document.querySelectorAll('input[type="password"]');
    
    passwordFields.forEach(field => {
        const meterContainer = field.parentNode.querySelector('#password-strength-meter');
        if (meterContainer) {
            new PasswordStrengthMeter(field, meterContainer);
        }
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PasswordStrengthMeter;
}
