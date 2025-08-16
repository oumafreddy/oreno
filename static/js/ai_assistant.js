/**
 * Enhanced AI Assistant JavaScript
 * Supports conversation history, user preferences, and improved UX
 */

class AIAssistant {
    constructor() {
        this.currentConversationId = null;
        this.sessionId = null;
        this.isLoading = false;
        this.conversationHistory = [];
        this.userPreferences = null;
        
        this.initializeElements();
        this.initializeEventListeners();
        this.loadUserPreferences();
    }

    initializeElements() {
        // Core elements
        this.aiButton = document.getElementById('ai-assistant-button');
        this.aiModalEl = document.getElementById('aiAssistantModal');
        this.form = document.getElementById('ai-assistant-form');
        this.questionInput = document.getElementById('ai-question');
        this.answerDiv = document.getElementById('ai-answer');
        this.answerText = document.getElementById('ai-answer-text');
        this.loadingDiv = document.getElementById('ai-loading');
        this.askBtn = document.getElementById('ai-ask-btn');
        
        // New elements for enhanced features
        this.conversationList = document.getElementById('ai-conversation-list');
        this.conversationContainer = document.getElementById('ai-conversation-container');
        this.newChatBtn = document.getElementById('ai-new-chat-btn');
        this.settingsBtn = document.getElementById('ai-settings-btn');
        this.analyticsBtn = document.getElementById('ai-analytics-btn');
        
        // Initialize modal
        this.initializeModal();
    }

    initializeModal() {
        if (this.aiModalEl && this.aiModalEl.classList.contains('modal')) {
            try {
                if (window.bootstrap && window.bootstrap.Modal) {
                    const existingInstance = bootstrap.Modal.getInstance(this.aiModalEl);
                    if (existingInstance) {
                        this.aiModal = existingInstance;
                    } else {
                        this.aiModal = new bootstrap.Modal(this.aiModalEl, {
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

        // Manage aria-hidden attribute
        if (this.aiModalEl) {
            this.aiModalEl.addEventListener('show.bs.modal', () => {
                this.aiModalEl.setAttribute('aria-hidden', 'false');
                this.loadConversationHistory();
            });
            this.aiModalEl.addEventListener('hidden.bs.modal', () => {
                this.aiModalEl.setAttribute('aria-hidden', 'true');
                this.resetConversation();
            });
        }
    }

    initializeEventListeners() {
        // AI Button click handler
        if (this.aiButton && this.aiModal) {
            this.aiButton.addEventListener('click', (e) => {
                e.preventDefault();
                try {
                    this.aiModal.show();
                } catch (error) {
                    console.error('Error showing AI Assistant modal:', error);
                }
            });
        }

        // Form submission
        if (this.form && this.questionInput && this.answerDiv && this.answerText && this.loadingDiv && this.askBtn) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleQuestionSubmission();
            });
        }

        // New chat button
        if (this.newChatBtn) {
            this.newChatBtn.addEventListener('click', () => {
                this.startNewConversation();
            });
        }

        // Settings button
        if (this.settingsBtn) {
            this.settingsBtn.addEventListener('click', () => {
                this.showSettings();
            });
        }

        // Analytics button
        if (this.analyticsBtn) {
            this.analyticsBtn.addEventListener('click', () => {
                this.showAnalytics();
            });
        }

        // Question input enhancements
        if (this.questionInput) {
            this.questionInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    e.preventDefault();
                    this.handleQuestionSubmission();
                }
            });
        }
    }

    async loadUserPreferences() {
        try {
            const response = await fetch('/api/ai/preferences/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.userPreferences = data.preferences;
                this.applyUserPreferences();
            }
        } catch (error) {
            console.error('Error loading user preferences:', error);
        }
    }

    applyUserPreferences() {
        if (!this.userPreferences) return;
        
        // Apply temperature and other settings to the UI
        if (this.questionInput) {
            this.questionInput.placeholder = this.userPreferences.context_window > 0 
                ? "Ask me anything about GRC, audit, risk, or compliance... (Ctrl+Enter to send)"
                : "Ask me anything about GRC, audit, risk, or compliance...";
        }
    }

    async handleQuestionSubmission() {
        const question = this.questionInput.value.trim();
        if (!question || this.isLoading) return;

        this.isLoading = true;
        this.showLoadingState();

        try {
            const response = await this.sendQuestion(question);
            this.handleResponse(response);
        } catch (error) {
            this.handleError(error);
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    async sendQuestion(question) {
        const payload = {
            question: question,
            session_id: this.sessionId,
            conversation_id: this.currentConversationId
        };

        const response = await fetch('/api/ai/ask/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    handleResponse(data) {
        if (data.response) {
            // Update conversation tracking
            this.currentConversationId = data.conversation_id;
            this.sessionId = data.session_id;
            
            // Display response
            this.answerText.innerHTML = this.formatResponse(data.response);
            this.answerDiv.classList.remove('d-none');
            
            // Add to conversation history
            this.addToConversationHistory('user', data.question);
            this.addToConversationHistory('assistant', data.response, data);
            
            // Clear input
            this.questionInput.value = '';
            
            // Update conversation list
            this.updateConversationList();
            
            // Show response metadata if available
            if (data.model_used && data.response_time) {
                this.showResponseMetadata(data);
            }
        } else if (data.error) {
            this.showError(`Error: ${data.error}`);
        }
    }

    formatResponse(response) {
        // Convert markdown-like formatting to HTML
        return response
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    addToConversationHistory(role, content, metadata = {}) {
        this.conversationHistory.push({
            role: role,
            content: content,
            timestamp: new Date(),
            metadata: metadata
        });
        
        this.updateConversationDisplay();
    }

    updateConversationDisplay() {
        if (!this.conversationContainer) return;
        
        const html = this.conversationHistory.map(message => {
            const isUser = message.role === 'user';
            const time = message.timestamp.toLocaleTimeString();
            
            return `
                <div class="ai-message ${isUser ? 'ai-message-user' : 'ai-message-assistant'}">
                    <div class="ai-message-content">
                        ${isUser ? message.content : this.formatResponse(message.content)}
                    </div>
                    <div class="ai-message-meta">
                        <small class="text-muted">${time}</small>
                        ${message.metadata.model_used ? `<small class="text-muted ms-2">${message.metadata.model_used}</small>` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        this.conversationContainer.innerHTML = html;
        this.conversationContainer.scrollTop = this.conversationContainer.scrollHeight;
    }

    showResponseMetadata(data) {
        const metadataHtml = `
            <div class="ai-response-metadata mt-2">
                <small class="text-muted">
                    Model: ${data.model_used} | 
                    Response time: ${data.response_time.toFixed(2)}s | 
                    Tokens: ${data.tokens_used}
                </small>
            </div>
        `;
        
        this.answerDiv.insertAdjacentHTML('beforeend', metadataHtml);
    }

    async loadConversationHistory() {
        try {
            const response = await fetch('/api/ai/conversations/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateConversationList(data.conversations);
            }
        } catch (error) {
            console.error('Error loading conversation history:', error);
        }
    }

    updateConversationList(conversations = []) {
        if (!this.conversationList) return;
        
        const html = conversations.map(conv => `
            <div class="ai-conversation-item" data-conversation-id="${conv.id}">
                <div class="ai-conversation-title">${conv.title}</div>
                <div class="ai-conversation-meta">
                    <small class="text-muted">
                        ${conv.message_count} messages | 
                        ${conv.total_tokens} tokens | 
                        ${new Date(conv.created_at).toLocaleDateString()}
                    </small>
                </div>
            </div>
        `).join('');
        
        this.conversationList.innerHTML = html;
        
        // Add click handlers
        this.conversationList.querySelectorAll('.ai-conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                this.loadConversation(item.dataset.conversationId);
            });
        });
    }

    async loadConversation(conversationId) {
        try {
            const response = await fetch('/api/ai/conversations/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ conversation_id: conversationId })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentConversationId = conversationId;
                this.conversationHistory = data.messages.map(msg => ({
                    role: msg.role,
                    content: msg.content,
                    timestamp: new Date(msg.created_at),
                    metadata: {
                        model_used: msg.model_used,
                        response_time: msg.response_time
                    }
                }));
                
                this.updateConversationDisplay();
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
        }
    }

    startNewConversation() {
        this.currentConversationId = null;
        this.sessionId = null;
        this.conversationHistory = [];
        this.updateConversationDisplay();
        this.answerDiv.classList.add('d-none');
        this.questionInput.focus();
    }

    async showSettings() {
        // Implementation for settings modal
        console.log('Show settings modal');
    }

    async showAnalytics() {
        try {
            const response = await fetch('/api/ai/analytics/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayAnalytics(data);
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    displayAnalytics(data) {
        // Implementation for analytics display
        console.log('Analytics data:', data);
    }

    showLoadingState() {
        this.answerDiv.classList.add('d-none');
        this.answerText.textContent = '';
        this.loadingDiv.classList.remove('d-none');
        this.askBtn.disabled = true;
        this.askBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Thinking...';
    }

    hideLoadingState() {
        this.loadingDiv.classList.add('d-none');
        this.askBtn.disabled = false;
        this.askBtn.innerHTML = '<i class="bi bi-send me-1"></i>Ask AI';
    }

    handleError(error) {
        console.error('AI Assistant error:', error);
        
        let errorMessage = 'Sorry, there was a problem contacting the AI assistant. Please try again.';
        
        if (error.message.includes('401')) {
            errorMessage = 'Please log in to use the AI assistant.';
        } else if (error.message.includes('500')) {
            errorMessage = 'The AI service is temporarily unavailable. Please try again later.';
        }
        
        this.showError(errorMessage);
    }

    showError(message) {
        this.answerText.innerHTML = `<div class="alert alert-danger">${message}</div>`;
        this.answerDiv.classList.remove('d-none');
    }

    resetConversation() {
        this.currentConversationId = null;
        this.sessionId = null;
        this.conversationHistory = [];
        this.answerDiv.classList.add('d-none');
        this.questionInput.value = '';
    }

    getCookie(name) {
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
}

// Initialize AI Assistant when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new AIAssistant();
}); 