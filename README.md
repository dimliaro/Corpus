# Corpus — EU Regulatory RAG

A focused Retrieval-Augmented Generation (RAG) service that answers
natural-language questions over EU regulation (GDPR) and returns
**grounded answers with references to the source articles and recitals**.

A cleaner, single-service take on the idea behind my bootcamp capstone —
built around a FastAPI backend, Azure AI Search and Azure OpenAI.

---

## What it does

You ask a plain-language question about the regulation (e.g. *"What is
personal data?"*); the service retrieves the most relevant passages from a
vector index and has an LLM compose a concise answer grounded **only** in those
passages, with citations — so the response is traceable, not invented.

---

## Architecture

```
                         Indexing (run once)
PDF ─► structure-aware chunking ─► embeddings ─► Azure AI Search (vector index)
        (recital / article)         (Azure OpenAI)

                         Query time (per request)
question ─► embedding ─► vector search (top-k) ─► LLM ─► grounded answer + sources
```

**Backend:** FastAPI exposes the query endpoint and serves a minimal frontend.
**Retrieval:** Azure AI Search vector query (k-nearest-neighbours).
**Generation:** Azure OpenAI composes the answer from the retrieved chunks.

---

## Key engineering decisions

- **Structure-aware chunking.** EU regulations follow a fixed structure —
  a preamble of numbered *recitals*, then *articles* grouped in chapters. Rather
  than splitting the text blindly every N words, the parser (`src/chunking.py`)
  produces **one chunk per recital and per article**, tagged with its type,
  number, title, chapter and page. Each chunk is therefore a self-contained,
  legally meaningful unit, which makes retrieval return coherent, citable
  passages instead of fragments.
- **Grounded answers with sources.** The LLM answers strictly from the retrieved
  chunks and the response carries the passages it used — important in a
  compliance context where an answer has to be defensible.

---

## Tech stack

**Python** · **FastAPI** · **Azure AI Search** (vector) ·
**Azure OpenAI** (embeddings + chat) · **PyMuPDF** · **Docker** · **uv**

---

## Repository structure

```
Corpus/
├── src/
│   ├── chunking.py      # structure-aware recital/article parser
│   ├── embedding.py     # Azure OpenAI embeddings
│   ├── saveToIndex.py   # push embedded chunks to Azure AI Search
│   ├── search.py        # vector retrieval (top-k)
│   ├── rag_api.py       # FastAPI app: /query, /chat, document upload
│   └── main.py
├── frontend/index.html  # minimal query UI
├── data/                # source regulation PDF (GDPR)
├── Dockerfile
└── docker-compose.yml
```

---

## Running it

> **Note.** This service needs external credentials — an **Azure AI Search**
> endpoint and an **Azure OpenAI** deployment. It was built with
> bootcamp-provisioned keys that are no longer active, so it doesn't run against
> those out of the box; point it at your own Azure resources via a `.env` file.

```bash
cd Corpus/
uv sync

# create Corpus/.env with your own credentials:
#   AI_SEARCH_ENDPOINT, AI_SEARCH_API_KEY
#   (Azure OpenAI endpoint / key / deployment for embeddings + chat)

cd src
uv run uvicorn rag_api:app --reload
```

Then open the frontend and ask a question about the regulation.

---

*Personal project, 2026 — an outgrowth of the Accenture × Code.Hub bootcamp work.*
