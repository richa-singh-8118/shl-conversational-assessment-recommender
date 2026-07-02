# Conversational SHL Assessment Recommender

A stateless, production-ready conversational AI agent that helps recruiters and hiring managers discover appropriate SHL assessments through natural conversation.

🚀 **Live Demo:** [https://shl-assessment-recommender.onrender.com](https://shl-assessment-recommender.onrender.com)

---

## Features

- 🧠 **Multi-Agent Architecture** — Classifier → Clarifier → Hybrid Retriever → LLM Reranker → Recommender
- 🔍 **Hybrid Search** — FAISS vector similarity + BM25-style keyword scoring merged with configurable weights
- 🛡️ **Strict Schema Compliance** — Every response always returns `reply`, `recommendations[]`, and `end_of_conversation`
- 🚫 **Refusal Mode** — Detects prompt injection, salary queries, legal/HR consulting, and non-SHL product requests
- 📊 **Comparison Mode** — Generates factual, catalog-grounded markdown comparison tables
- 🔁 **Refinement Support** — Tracks full conversation history to handle mid-conversation preference changes
- 🤖 **Gemini-Powered** — Uses `gemini-1.5-flash` via the Google Generative AI SDK; falls back to heuristic simulation when no API key is set
- 🐳 **Docker-Ready** — Self-contained image that pre-builds the FAISS index at build time

---

## Project Structure

```
.
├── app.py                   # FastAPI entrypoint
├── build_index.py           # FAISS index builder
├── catalog/
│   ├── catalog.json         # Curated SHL product catalog (20 assessments)
│   ├── scraper.py           # SHL catalog scraper with curated fallback
│   ├── index.faiss          # Pre-built FAISS vector index (generated)
│   └── index_metadata.json  # Assessment metadata mapping (generated)
├── agents/
│   ├── llm_client.py        # Gemini API wrapper + heuristic fallback
│   ├── classifier.py        # Classifies intent: REFUSAL / COMPARISON / RECOMMENDATION
│   ├── clarifier.py         # Extracts context; asks for missing role/seniority
│   ├── recommender.py       # Orchestrates retrieval, reranking, and explanation
│   ├── comparison.py        # Generates factual catalog comparison tables
│   └── refusal.py           # Returns standard refusal responses
├── retrieval/
│   ├── vectorstore.py       # FAISS index loader + similarity search
│   ├── hybrid_search.py     # Vector + keyword hybrid scoring
│   └── reranker.py          # LLM-based candidate reranking
├── models/
│   └── schemas.py           # Strict Pydantic request/response schemas
├── tests/
│   ├── test_health.py
│   ├── test_chat.py
│   ├── test_refusal.py
│   ├── test_comparison.py
│   └── test_refinement.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Setup & Running Locally

### 1. Clone & Install Dependencies

```bash
git clone <your-repo-url>
cd "Conversational SHL Assessment Recommender"
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
```

### 3. Build the FAISS Index

```bash
python catalog/scraper.py   # Populates catalog/catalog.json
python build_index.py        # Builds FAISS index
```

### 4. Start the Server

```bash
python app.py
# Or with uvicorn directly:
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at: `http://localhost:8000`  
Interactive docs at: `http://localhost:8000/docs`

---

## API Reference

### `GET /health`

```json
{"status": "ok"}
```

### `POST /chat`

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "I need to hire a Senior Java Developer"}
  ]
}
```

**Response (strict schema):**
```json
{
  "reply": "Based on your Senior Java Developer requirements, I recommend...",
  "recommendations": [
    {
      "name": "SHL Coding Simulations (Java)",
      "url": "https://www.shl.com/products/assessments/skills-and-simulations/coding-simulations/",
      "test_type": "Skills & Simulations"
    }
  ],
  "end_of_conversation": true
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Docker Deployment

```bash
docker build -t shl-recommender .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key shl-recommender
```

---

## Agent Decision Flow

```
User Message
     │
     ▼
[Classifier Agent]
     │
     ├── REFUSAL ──────────────► [Refusal Agent] ──► Response
     │
     ├── COMPARISON ───────────► [Comparison Agent] ──► Response
     │
     └── RECOMMENDATION
              │
              ▼
         [Clarifier Agent]
              │
              ├── Missing Role ──────► Ask for Role ──► Response
              ├── Missing Seniority ─► Ask for Seniority ──► Response
              │
              └── Context Complete
                       │
                       ▼
               [Hybrid Search]
               (FAISS + Keyword)
                       │
                       ▼
               [LLM Reranker]
                       │
                       ▼
               [Recommender Agent] ──► Response
```

---

## Catalog Coverage

The system covers **20 SHL Individual Test Solutions**:

| Category | Assessments |
|---|---|
| **Personality** | OPQ32r, Motivation Questionnaire (MQ) |
| **Cognitive** | Verify Inductive, Numerical, Verbal, Deductive, Spatial, Mechanical, G+ |
| **Behavioral** | GSA, SJT |
| **Skills & Simulations** | Coding (Java, Python, React, SQL), Technical (AWS, Linux), Business (Excel), Language (English), Call Center |
