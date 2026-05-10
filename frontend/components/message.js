const MessageBuilder = {
    createUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'message user';
        div.innerHTML = `
            <div class="message-bubble">${this.escapeHTML(text)}</div>
        `;
        return div;
    },

    createBotMessage(text, sources = []) {
        const div = document.createElement('div');
        div.className = 'message bot';
        
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            const uniqueSources = new Map();
            sources.forEach(s => uniqueSources.set(s.repo_name, s.repo_url));
            
            const sourceLinks = Array.from(uniqueSources.entries()).map(([name, url]) => 
                `<span class="source-item"><a href="${url}" target="_blank">${this.escapeHTML(name)}</a></span>`
            ).join('');
            
            if (sourceLinks) {
                sourcesHtml = `<div class="sources">Sources: ${sourceLinks}</div>`;
            }
        }

        // Replace basic markdown (bold, newlines)
        let formattedText = this.escapeHTML(text)
            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
            .replace(/\\n/g, '<br>');

        div.innerHTML = `
            <div class="message-bubble">
                <div class="content">${formattedText}</div>
                ${sourcesHtml}
            </div>
        `;
        return div;
    },

    createTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message bot typing-message';
        div.innerHTML = `
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        return div;
    },

    escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
};
