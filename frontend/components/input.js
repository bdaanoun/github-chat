const InputUI = {
    init() {
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
    },

    enable() {
        this.chatInput.disabled = false;
        this.sendBtn.disabled = false;
        this.chatInput.focus();
    },

    disable() {
        this.chatInput.disabled = true;
        this.sendBtn.disabled = true;
    },

    clear() {
        this.chatInput.value = '';
    },
    
    getValue() {
        return this.chatInput.value.trim();
    }
};
