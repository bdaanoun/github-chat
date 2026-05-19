const MessageBuilder = {
    // GitHub icon SVG for bot avatar
    _botAvatarSVG: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
    </svg>`,

    _userAvatarSVG: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
    </svg>`,

    _githubIconSVG: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>
    </svg>`,

    createUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'message user';
        div.innerHTML = `
            <div class="message-avatar">${this._userAvatarSVG}</div>
            <div class="message-bubble">${this.escapeHTML(text)}</div>
        `;
        return div;
    },

    createBotMessage(text, sources = []) {
        const div = document.createElement('div');
        div.className = 'message bot';

        // Sources HTML
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            const uniqueSources = new Map();
            sources.forEach(s => uniqueSources.set(s.repo_name, s.repo_url));

            const chips = Array.from(uniqueSources.entries()).map(([name, url]) =>
                `<span class="source-chip">
                    ${this._githubIconSVG}
                    <a href="${url}" target="_blank" rel="noopener noreferrer">${this.escapeHTML(name)}</a>
                 </span>`
            ).join('');

            if (chips) {
                sourcesHtml = `<div class="sources">
                    <span class="sources-label">Sources</span>
                    ${chips}
                </div>`;
            }
        }

        div.innerHTML = `
            <div class="message-avatar">${this._botAvatarSVG}</div>
            <div class="message-bubble">
                <div class="content">${this.formatMarkdown(text)}</div>
                ${sourcesHtml}
            </div>
        `;
        return div;
    },

    createTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message bot typing-message';
        div.innerHTML = `
            <div class="message-avatar">${this._botAvatarSVG}</div>
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        return div;
    },

    /**
     * Simple but effective markdown formatter.
     * Handles: bold, italic, inline code, code blocks, headers, bullet lists, line breaks.
     */
    formatMarkdown(text) {
        // Escape HTML first
        let out = this.escapeHTML(text);

        // Code blocks (``` ... ```)
        out = out.replace(/```[\w]*\n?([\s\S]*?)```/g, (_, code) =>
            `<pre><code>${code.trim()}</code></pre>`
        );

        // Bold (**text**)
        out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Italic (*text* or _text_) — only single asterisk/underscore
        out = out.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
        out = out.replace(/_([^_\n]+)_/g, '<em>$1</em>');

        // Inline code (`code`)
        out = out.replace(/`([^`\n]+)`/g, '<code>$1</code>');

        // Headers (### H3, ## H2, # H1)
        out = out.replace(/^### (.+)$/gm, '<h4 style="margin:10px 0 4px;font-size:0.95rem;color:var(--text)">$1</h4>');
        out = out.replace(/^## (.+)$/gm,  '<h3 style="margin:12px 0 6px;font-size:1rem;color:var(--text)">$1</h3>');
        out = out.replace(/^# (.+)$/gm,   '<h2 style="margin:14px 0 8px;font-size:1.1rem;color:var(--text)">$1</h2>');

        // Bullet lists (lines starting with - or *)
        out = out.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
        out = out.replace(/(<li>.*<\/li>\n?)+/g, match => `<ul>${match}</ul>`);

        // Numbered lists
        out = out.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

        // Paragraphs: double newlines to <p>
        const parts = out.split(/\n{2,}/);
        out = parts.map(block => {
            block = block.trim();
            if (!block) return '';
            if (/^<(h[1-4]|ul|ol|li|pre)/.test(block)) return block;
            // Single newlines within paragraph → <br>
            return `<p>${block.replace(/\n/g, '<br>')}</p>`;
        }).join('');

        return out;
    },

    escapeHTML(str) {
        return String(str).replace(/[&<>'"]/g,
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }
};
