const Store = {
    state: {
        currentUsername: null,
        isContextLoaded: false,
        reposIndexed: 0,
        chunksCreated: 0
    },

    setContext(username, repos, chunks) {
        this.state.currentUsername = username;
        this.state.reposIndexed = repos;
        this.state.chunksCreated = chunks;
        this.state.isContextLoaded = true;
    },

    getContext() {
        return this.state;
    },

    clearContext() {
        this.state.currentUsername = null;
        this.state.isContextLoaded = false;
        this.state.reposIndexed = 0;
        this.state.chunksCreated = 0;
    }
};
