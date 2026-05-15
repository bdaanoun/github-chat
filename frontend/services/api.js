const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API = {
    // Automatically switch between local testing and production
    BASE_URL: isLocal ? "http://localhost:8000/api" : "https://github-rag-backend.onrender.com/api",

    async loadProfile(username) {
        const response = await fetch(`${this.BASE_URL}/profile/load`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Failed to load profile");
        }
        return data;
    },

    async askQuestion(username, question) {
        const response = await fetch(`${this.BASE_URL}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, question })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Failed to fetch answer");
        }
        return data;
    }
};
