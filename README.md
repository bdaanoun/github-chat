# GitHub RAG AI Assistant

A full-stack **Retrieval-Augmented Generation (RAG)** application that lets you chat with an AI about any GitHub developer's public repositories. Load a user's profile, and the system fetches, chunks, embeds, and indexes their repo data — then answers your questions using only that context.

---

## ✨ Features

- **Profile Ingestion** — Fetches all public repos + READMEs for any GitHub user via the GitHub API.
- **RAG Pipeline** — Chunks text, generates embeddings with `all-MiniLM-L6-v2`, and stores them in an in-memory FAISS index.
- **Context-Aware Chat** — Questions are answered strictly from retrieved repository context — no hallucination.
- **Ollama-Powered LLM** — Uses a locally-running Ollama model for answer generation (no cloud API keys needed).
- **Modern Frontend** — Clean, responsive chat UI built with vanilla HTML/CSS/JS.

---

## 🏗️ Architecture

```
frontend/          → Vanilla JS chat interface (served via static file server)
backend/
├── api/           → FastAPI route handlers (profile loading, Q&A)
├── config/        → App settings & environment config
├── github/        → GitHub API client & data parser
├── models/        → Pydantic request/response schemas
├── rag/           → RAG pipeline (chunker, embedder, retriever, LLM client, prompt builder)
├── utils/         → Logging utilities
└── vector/        → FAISS vector store (in-memory, per-user indexes)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Ollama** — Install from [ollama.com](https://ollama.com) and pull a model:
  ```bash
  ollama pull llama3
  ```
- **GitHub Token** _(optional)_ — Increases API rate limits. Generate one at [github.com/settings/tokens](https://github.com/settings/tokens).

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd github-chat

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# GitHub (optional — increases rate limits)
GITHUB_TOKEN=ghp_your_token_here

# Ollama LLM Configuration
OPENAI_API_KEY=ollama
OPENAI_API_BASE=http://localhost:11434/v1
LLM_MODEL=llama3
```

> **Note:** Ollama exposes an OpenAI-compatible API at `http://localhost:11434/v1`, so no code changes are required — just set the environment variables above.

### 3. Start the Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Start the Frontend

```bash
cd frontend
python3 -m http.server 3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 💬 Usage

1. Enter a **GitHub username** in the sidebar and click **Load Context**.
2. Wait for the system to fetch repos, chunk text, and build the vector index.
3. Ask questions in the chat — the AI answers based only on the loaded repository data.

---

## ⚙️ Configuration

All settings are managed via environment variables or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `GITHUB_TOKEN` | `""` | GitHub personal access token (optional) |
| `OPENAI_API_KEY` | `"sk-placeholder"` | API key (set to `ollama` for Ollama) |
| `OPENAI_API_BASE` | `""` | LLM API base URL (`http://localhost:11434/v1` for Ollama) |
| `LLM_MODEL` | `"gpt-3.5-turbo"` | Model name (`llama3`, `mistral`, etc.) |
| `EMBEDDING_MODEL` | `"all-MiniLM-L6-v2"` | Sentence-transformer model for embeddings |
| `CHUNK_SIZE` | `500` | Characters per text chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between consecutive chunks |
| `TOP_K_RETRIEVAL` | `5` | Number of context chunks to retrieve |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, Uvicorn |
| **LLM** | Ollama (OpenAI-compatible API) |
| **Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **Vector Store** | FAISS (in-memory) |
| **Frontend** | Vanilla HTML / CSS / JavaScript |
| **Data Source** | GitHub REST API |

---

## 📄 License

This project is for educational and portfolio purposes.
