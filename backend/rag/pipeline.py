
from github.client import fetch_repos
from rag.chunker import chunk_text
from rag.embedder import embed
from rag.store import VectorStore
from sentence_transformers import SentenceTransformer

stores = {}

embedder = SentenceTransformer("all-MiniLM-L6-v2")


def build_index(username, repos):
    texts = []

    for r in repos:
        content = f"""
        Name: {r.get('name')}
        Description: {r.get('description')}
        Language: {r.get('language')}
        URL: {r.get('html_url')}
        """

        chunks = chunk_text(content)
        texts.extend(chunks)

    vectors = embedder.encode(texts)

    store = VectorStore()
    store.add(vectors, texts)

    stores[username] = store


def answer_question(username, question):
    store = stores.get(username)

    if not store:
        return "No data loaded for this user."

    q_vec = embedder.encode([question])[0]
    results = store.search(q_vec)

    context = "\n".join(results)

    # simple LLM stub (replace with OpenAI/Ollama later)
    return f"""
Based on GitHub data:

{context}

Answer: The developer works on the above projects and technologies.
"""