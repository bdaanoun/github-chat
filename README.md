cat > README.md << 'EOF'
---
title: Github Chat
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# GitHub RAG AI Assistant

A full-stack **Retrieval-Augmented Generation (RAG)** application that lets you chat with an AI about any GitHub developer's public repositories. Load a user's profile, and the system fetches, chunks, embeds, and indexes their repo data — then answers your questions using only that context.

---

## ✨ Features

- **Profile Ingestion** — Fetches all public repos + READMEs for any GitHub user via the GitHub API.
- **RAG Pipeline** — Chunks text, generates embeddings with `all-MiniLM-L6-v2`, and stores them in an in-memory FAISS index.
- **Context-Aware Chat** — Questions are answered strictly from retrieved repository context — no hallucination.
- **Modern Frontend** — Clean, responsive chat UI built with vanilla HTML/CSS/JS.

---

## 📄 License

This project is for educational and portfolio purposes.