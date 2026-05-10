const ChatUI = {
    init() {
        this.chatHistory = document.getElementById('chat-history');
        this.loadForm = document.getElementById('load-profile-form');
        this.usernameInput = document.getElementById('github-username');
        this.loadSpinner = document.getElementById('load-spinner');
        this.loadStatus = document.getElementById('load-status');
        this.contextInfo = document.getElementById('context-info');
        this.contextName = document.getElementById('context-name');
        this.contextStats = document.getElementById('context-stats');
        this.contextAvatar = document.getElementById('context-avatar');
        
        this.chatStatus = document.getElementById('chat-status-indicator');
        this.chatForm = document.getElementById('chat-input-form');
        
        InputUI.init();
        
        this.bindEvents();
    },

    bindEvents() {
        this.loadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = this.usernameInput.value.trim();
            if(!username) return;
            
            await this.handleLoadProfile(username);
        });

        this.chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const question = InputUI.getValue();
            if(!question) return;
            
            await this.handleAskQuestion(question);
        });
    },

    async handleLoadProfile(username) {
        this.setLoadingState(true);
        this.loadStatus.className = 'status-message';
        this.loadStatus.textContent = 'Fetching and parsing GitHub repos... This may take a minute depending on their size.';
        
        try {
            const data = await API.loadProfile(username);
            Store.setContext(username, data.repos_indexed, data.chunks_created);
            
            this.loadStatus.textContent = `Success! Mapped ${data.repos_indexed} repos.`;
            this.loadStatus.className = 'status-message success';
            this.updateContextUI(username, data);
            
            InputUI.enable();
            this.chatStatus.textContent = 'Ready';
            this.chatStatus.className = 'status-indicator ready';
            
            this.appendMessage(MessageBuilder.createBotMessage(`I've analyzed ${username}'s repositories and created a semantic map. What would you like to know about their work?`));
            
        } catch (err) {
            this.loadStatus.textContent = err.message;
            this.loadStatus.className = 'status-message error';
            InputUI.disable();
            Store.clearContext();
            this.contextInfo.classList.add('hidden');
        } finally {
            this.setLoadingState(false);
        }
    },

    async handleAskQuestion(question) {
        const state = Store.getContext();
        if(!state.isContextLoaded) return;
        
        InputUI.clear();
        InputUI.disable();
        
        // Append user msg
        this.appendMessage(MessageBuilder.createUserMessage(question));
        
        // Append typing indicator
        const typingIndicator = MessageBuilder.createTypingIndicator();
        this.appendMessage(typingIndicator);
        
        try {
            const data = await API.askQuestion(state.currentUsername, question);
            
            // Remove typing indicator
            typingIndicator.remove();
            
            // Append bot response
            this.appendMessage(MessageBuilder.createBotMessage(data.answer, data.sources));
        } catch (err) {
            typingIndicator.remove();
            this.appendMessage(MessageBuilder.createBotMessage("Sorry, I encountered an error: " + err.message));
        } finally {
            InputUI.enable();
        }
    },

    setLoadingState(isLoading) {
        const loadBtn = document.getElementById('load-profile-btn');
        if(isLoading) {
            loadBtn.disabled = true;
            this.loadSpinner.classList.remove('hidden');
        } else {
            loadBtn.disabled = false;
            this.loadSpinner.classList.add('hidden');
        }
    },

    updateContextUI(username, data) {
        this.contextInfo.classList.remove('hidden');
        this.contextName.textContent = username;
        this.contextAvatar.src = `https://github.com/${username}.png`;
        this.contextStats.textContent = `${data.repos_indexed} Repos | ${data.chunks_created} Context Chunks`;
        
        // Clear initial welcome message if present
        const welcome = this.chatHistory.querySelector('.welcome-message');
        if(welcome) welcome.remove();
    },

    appendMessage(element) {
        this.chatHistory.appendChild(element);
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    ChatUI.init();
});
