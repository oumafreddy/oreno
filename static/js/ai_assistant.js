// AI Assistant popup and form logic (CSP-compliant)
document.addEventListener('DOMContentLoaded', function() {
    const aiButton = document.getElementById('ai-assistant-button');
    const aiModalEl = document.getElementById('aiAssistantModal');
    let aiModal = null;
    
    // Only initialize modal if the element exists and doesn't already have an instance
    if (aiModalEl && aiModalEl.classList.contains('modal')) {
        try {
            // Check if Bootstrap is available
            if (window.bootstrap && window.bootstrap.Modal) {
                // Check if modal already has an instance
                const existingInstance = bootstrap.Modal.getInstance(aiModalEl);
                if (existingInstance) {
                    aiModal = existingInstance;
                } else {
                    // Create new instance with proper configuration
                    aiModal = new bootstrap.Modal(aiModalEl, {
                        backdrop: true,
                        keyboard: true,
                        focus: true
                    });
                }
            } else {
                console.warn('Bootstrap Modal not available');
            }
        } catch (error) {
            console.error('Error initializing AI Assistant modal:', error);
        }
    }
    
    const form = document.getElementById('ai-assistant-form');
    const questionInput = document.getElementById('ai-question');
    const answerDiv = document.getElementById('ai-answer');
    const answerText = document.getElementById('ai-answer-text');
    const loadingDiv = document.getElementById('ai-loading');
    const askBtn = document.getElementById('ai-ask-btn');

    // Manually manage aria-hidden attribute to prevent accessibility warnings
    if (aiModalEl) {
        aiModalEl.addEventListener('show.bs.modal', function () {
            this.setAttribute('aria-hidden', 'false');
        });
        aiModalEl.addEventListener('hidden.bs.modal', function () {
            this.setAttribute('aria-hidden', 'true');
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function sanitizeInput(input) {
        // Basic input sanitization
        return input.replace(/<[^>]*>/g, '').trim();
    }

    function showError(message) {
        answerText.textContent = message;
        answerDiv.classList.remove('d-none');
        answerDiv.classList.remove('alert-info');
        answerDiv.classList.add('alert-danger');
    }

    function showSuccess(message) {
        answerText.textContent = message;
        answerDiv.classList.remove('d-none');
        answerDiv.classList.remove('alert-danger');
        answerDiv.classList.add('alert-info');
    }

    function resetForm() {
        questionInput.value = '';
        answerDiv.classList.add('d-none');
        askBtn.disabled = false;
    }

    // Only add click handler if both button and modal exist
    if (aiButton && aiModal) {
        aiButton.addEventListener('click', function(e) {
            e.preventDefault();
            try {
                aiModal.show();
            } catch (error) {
                console.error('Error showing AI Assistant modal:', error);
            }
        });
    }

    // Only attach form logic if the form exists (i.e., user is authenticated)
    if (form && questionInput && answerDiv && answerText && loadingDiv && askBtn) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const rawQuestion = questionInput.value.trim();
            if (!rawQuestion) {
                showError('Please enter a question.');
                return;
            }
            
            // Sanitize input
            const question = sanitizeInput(rawQuestion);
            if (question.length < 3) {
                showError('Question must be at least 3 characters long.');
                return;
            }
            
            if (question.length > 1000) {
                showError('Question must be less than 1000 characters.');
                return;
            }
            
            // Hide answer and show loading
            answerDiv.classList.add('d-none');
            answerText.textContent = '';
            loadingDiv.classList.remove('d-none');
            askBtn.disabled = true;

            // Add timeout for request
            const timeoutId = setTimeout(() => {
                loadingDiv.classList.add('d-none');
                askBtn.disabled = false;
                showError('Request timed out. Please try again.');
            }, 30000); // 30 second timeout

            fetch('/api/ai/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ question })
            })
            .then(response => {
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    if (response.status === 429) {
                        throw new Error('Rate limit exceeded. Please wait a moment before trying again.');
                    } else if (response.status === 401) {
                        throw new Error('Please log in to use the AI assistant.');
                    } else if (response.status === 400) {
                        return response.json().then(data => {
                            throw new Error(data.error || 'Invalid request.');
                        });
                    } else {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                }
                return response.json();
            })
            .then(data => {
                loadingDiv.classList.add('d-none');
                askBtn.disabled = false;
                
                if (data.response) {
                    // Success - show the AI response
                    showSuccess(data.response);
                } else if (data.error) {
                    // Error from the server
                    showError(`Error: ${data.error}`);
                } else {
                    // Unexpected response format
                    showError('Sorry, I received an unexpected response format.');
                }
            })
            .catch(error => {
                clearTimeout(timeoutId);
                loadingDiv.classList.add('d-none');
                askBtn.disabled = false;
                console.error('AI Assistant error:', error);
                
                if (error.message.includes('Rate limit')) {
                    showError(error.message);
                } else if (error.message.includes('401')) {
                    showError('Please log in to use the AI assistant.');
                } else if (error.message.includes('500')) {
                    showError('The AI service is temporarily unavailable. Please try again later.');
                } else {
                    showError(error.message || 'Sorry, there was a problem contacting the AI assistant. Please try again.');
                }
            });
        });

        // Add input validation on typing
        questionInput.addEventListener('input', function() {
            const question = this.value.trim();
            if (question.length > 1000) {
                this.setCustomValidity('Question must be less than 1000 characters.');
            } else if (question.length > 0 && question.length < 3) {
                this.setCustomValidity('Question must be at least 3 characters long.');
            } else {
                this.setCustomValidity('');
            }
        });

        // Reset form when modal is hidden
        aiModalEl.addEventListener('hidden.bs.modal', function () {
            resetForm();
        });
    }
}); 