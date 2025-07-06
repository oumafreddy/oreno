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
            const question = questionInput.value.trim();
            if (!question) return;
            
            // Hide answer and show loading
            answerDiv.classList.add('d-none');
            answerText.textContent = '';
            loadingDiv.classList.remove('d-none');
            askBtn.disabled = true;

            fetch('/api/ai/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ question })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                loadingDiv.classList.add('d-none');
                askBtn.disabled = false;
                
                if (data.response) {
                    // Success - show the AI response
                    answerText.textContent = data.response;
                    answerDiv.classList.remove('d-none');
                } else if (data.error) {
                    // Error from the server
                    answerText.textContent = `Error: ${data.error}`;
                    answerDiv.classList.remove('d-none');
                } else {
                    // Unexpected response format
                    answerText.textContent = 'Sorry, I received an unexpected response format.';
                    answerDiv.classList.remove('d-none');
                }
            })
            .catch(error => {
                loadingDiv.classList.add('d-none');
                askBtn.disabled = false;
                console.error('AI Assistant error:', error);
                
                if (error.message.includes('401')) {
                    answerText.textContent = 'Please log in to use the AI assistant.';
                } else if (error.message.includes('500')) {
                    answerText.textContent = 'The AI service is temporarily unavailable. Please try again later.';
                } else {
                    answerText.textContent = 'Sorry, there was a problem contacting the AI assistant. Please try again.';
                }
                answerDiv.classList.remove('d-none');
            });
        });
    }
}); 