const ChatUI = {
    init() {
        // Sidebar elements
        this.loadForm        = document.getElementById('load-profile-form');
        this.usernameInput   = document.getElementById('github-username');
        this.loadSpinner     = document.getElementById('load-spinner');
        this.loadBtnText     = document.getElementById('load-btn-text');
        this.loadStatus      = document.getElementById('load-status');
        this.contextInfo     = document.getElementById('context-info');
        this.contextName     = document.getElementById('context-name');
        this.contextAvatar   = document.getElementById('context-avatar');
        this.statRepos       = document.getElementById('stat-repos');
        this.statChunks      = document.getElementById('stat-chunks');

        // Header / chat
        this.chatStatusBadge = document.getElementById('chat-status-indicator');
        this.chatStatusText  = document.getElementById('chat-status-text');
        this.chatHistory     = document.getElementById('chat-history');
        this.chatForm        = document.getElementById('chat-input-form');

        InputUI.init();
        this.bindEvents();
    },

    bindEvents() {
        // Load profile
        this.loadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = this.usernameInput.value.trim();
            if (!username) return;
            await this.handleLoadProfile(username);
        });

        // Chat submit
        this.chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const question = InputUI.getValue();
            if (!question) return;
            await this.handleAskQuestion(question);
        });

        // Welcome chip clicks
        document.querySelectorAll('.chip[data-question]').forEach(chip => {
            chip.addEventListener('click', () => {
                if (!Store.getContext().isContextLoaded) return;
                const q = chip.dataset.question;
                this.handleAskQuestion(q);
            });
        });
    },

    async handleLoadProfile(username) {
        this.setLoadingState(true);
        this.loadStatus.className = 'status-message loading';
        this.loadStatus.textContent = 'Fetching and indexing repos… this may take a moment.';

        try {
            const data = await API.loadProfile(username);
            Store.setContext(username, data.repos_indexed, data.chunks_created);

            this.loadStatus.textContent = `✓ Indexed ${data.repos_indexed} repos successfully.`;
            this.loadStatus.className = 'status-message success';
            this.updateContextUI(username, data);

            InputUI.enable();
            this.setStatus('ready', 'Ready');

            this.appendMessage(
                MessageBuilder.createBotMessage(
                    `I've analysed **${username}**'s repositories and built a semantic index with **${data.chunks_created}** context chunks. What would you like to know about their work?`
                )
            );
        } catch (err) {
            this.loadStatus.textContent = `✗ ${err.message}`;
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
        if (!state.isContextLoaded) return;

        InputUI.clear();
        InputUI.disable();
        this.setStatus('thinking', 'Thinking…');

        // Remove welcome screen if still present
        const welcome = this.chatHistory.querySelector('.welcome-screen');
        if (welcome) welcome.remove();

        this.appendMessage(MessageBuilder.createUserMessage(question));

        const typingIndicator = MessageBuilder.createTypingIndicator();
        this.appendMessage(typingIndicator);

        try {
            const data = await API.askQuestion(state.currentUsername, question);
            typingIndicator.remove();
            this.appendMessage(MessageBuilder.createBotMessage(data.answer, data.sources));
        } catch (err) {
            typingIndicator.remove();
            this.appendMessage(MessageBuilder.createBotMessage(`Sorry, I ran into an error: ${err.message}`));
        } finally {
            InputUI.enable();
            this.setStatus('ready', 'Ready');
        }
    },

    setStatus(type, text) {
        this.chatStatusBadge.className = `status-badge ${type}`;
        this.chatStatusText.textContent = text;
    },

    setLoadingState(isLoading) {
        const loadBtn = document.getElementById('load-profile-btn');
        if (isLoading) {
            loadBtn.disabled = true;
            this.loadSpinner.classList.remove('hidden');
            this.loadBtnText.textContent = 'Analysing…';
        } else {
            loadBtn.disabled = false;
            this.loadSpinner.classList.add('hidden');
            this.loadBtnText.textContent = 'Analyse Profile';
        }
    },

    updateContextUI(username, data) {
        this.contextInfo.classList.remove('hidden');
        this.contextName.textContent = username;
        this.contextAvatar.src = `https://github.com/${username}.png`;
        this.statRepos.textContent   = data.repos_indexed;
        this.statChunks.textContent  = data.chunks_created;

        // Remove welcome screen
        const welcome = this.chatHistory.querySelector('.welcome-screen');
        if (welcome) welcome.remove();
    },

    appendMessage(element) {
        this.chatHistory.appendChild(element);
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    ChatUI.init();
});
