// AI Assistant popup and form logic (CSP-compliant)
document.addEventListener('DOMContentLoaded', function() {
    const aiButton = document.getElementById('ai-assistant-button');
    const aiPopup = document.getElementById('ai-assistant-popup');
    const form = document.getElementById('ai-assistant-form');
    const input = document.getElementById('ai-assistant-input');
    const response = document.getElementById('ai-assistant-response');

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

    if (aiButton && aiPopup) {
        aiButton.addEventListener('click', function() {
            aiPopup.classList.toggle('show');
        });
    }

    // Only attach form logic if the form exists (i.e., user is authenticated)
    if (form && input && response) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            response.textContent = 'Thinking...';
            fetch('/services/ai/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ question: input.value })
            })
            .then(res => {
                if (!res.ok) throw new Error('Network response was not ok');
                return res.json();
            })
            .then(data => {
                response.textContent = data.response;
            })
            .catch(() => {
                response.textContent = 'Sorry, something went wrong.';
            });
        });
    }
}); 