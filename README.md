![CI](https://github.com/yourname/clinicalmind/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12)
![License](https://img.shields.io/badge/license-MIT-green)

# ClinicalMind

> Multi-hop agentic RAG over clinical trial data — with conflict detection, evidence chains, and production monitoring

**[Live Demo](https://clinicalmind-streamlit-483186754561.us-west1.run.app)** 
(P.S. The demo is delayed in response as it runs on GCP cloud run service and uses a FUSE mounted Database)

---

## What this is

ClinicalMind answers complex questions that span multiple clinical trials — questions that require retrieval, cross-study comparison, and conflict detection before a reliable answer can be synthesized.

The target conditions for the scope of the project are:
Rheumatoid Arthritis, Non-Small Cell Lung Cancer, Type 2 Diabetes, Heart Failure

A researcher asking *"Which Phase 3 trials for Type 2 Diabetes since 2020 showed HbA1c reduction greater than 1%, and how did dropout rates compare to SGLT2 trials?"* needs evidence pulled from multiple studies, compared, and reconciled — not a single-document lookup. Standard RAG fails here because it retrieves from one or two documents and generates an answer without awareness of what other trials exist or whether they agree.

ClinicalMind is built as a production system, not a notebook demo: a 4-node LangGraph agent, hybrid retrieval, per-query evaluation scoring, a monitored API, and a CI/CD pipeline that deploys to Google Cloud Run on every merge.

## Example queries it handles

```
"Which Phase 3 GLP-1 trials since 2021 showed HbA1c reduction > 1%,
 and how did dropout rates compare across them?"

"Do trials for semaglutide show consistent cardiovascular outcomes,
 or do results conflict between trials with different baseline HbA1c?"

"Which sponsors run trials for both Type 2 Diabetes and Heart Failure
 using SGLT2 inhibitors, and do their safety profiles agree?"
```

## Architecture

```
ClinicalTrials.gov API (16K+ trials)
        │
        ▼
┌─────────────────────────────────────┐
│         Ingestion Pipeline          │
│  Structured fields  → SQLite        │
│  Protocol text       → FAISS        │
└─────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────┐
│              LangGraph Agent (4 nodes)               │
│                                                      │
│  [1] Query Decomposer                                │
│       Breaks complex queries into atomic sub-queries │
│                                                      │
│  [2] Parallel Retriever                              │
│       SQL tool (structured) + Vector tool (semantic) │
│       BM25 hybrid search                             │
│                                                      │
│  [3] Conflict Detector                               │
│       Flags when trials report contradictory outcomes│
│                                                      │
│  [4] Citation Synthesizer                            │
│       Final answer + source NCT IDs + confidence     │
└──────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────┐
│       Evaluation Layer             │
│  RAGAS: faithfulness, relevancy,   │
│  context recall — logged per query │
└────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│     FastAPI Inference Layer     │
│  Pydantic-validated responses   │
│  Streamlit demo UI              │
└─────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│   Monitoring + CI/CD              │
│  Cloud Monitoring + Grafana Cloud │
│  GitHub Actions → Cloud Run       │
└───────────────────────────────────┘
```

## What makes this different from basic RAG

| | Typical portfolio RAG project | ClinicalMind |
|---|---|---|
| Retrieval | Single vector search | Hybrid SQL + dense + BM25, run in parallel |
| Reasoning | Single-pass | Multi-hop via 4-node LangGraph agent |
| Conflicts | Not handled | Dedicated node flags contradictory evidence |
| Evaluation | None | RAGAS scored and logged on every query |
| Deployment | Local notebook | Live on Cloud Run with CI/CD |
| Monitoring | None | Cloud Monitoring + Grafana dashboard |

## Tech stack

| Layer | Technology |
|---|---|
| Agent framework | LangGraph, LangChain |
| LLM | GPT-4o / Groq (Llama 3) |
| Retrieval | FAISS, BM25 hybrid search, Cohere Rerank |
| Structured data | SQLite |
| Evaluation | RAGAS (faithfulness, relevancy, context recall) |
| API | FastAPI, Pydantic |
| Demo UI | Streamlit |
| Containerization | Docker |
| Cloud | Google Cloud Run, Cloud Storage, Artifact Registry |
| Monitoring | Cloud Monitoring, Grafana Cloud |
| CI/CD | GitHub Actions |

## Dataset

[ClinicalTrials.gov](https://clinicaltrials.gov) — a free, public REST API maintained by the U.S. National Library of Medicine, covering 500,000+ registered clinical studies. This project indexes completed Phase 2/3 trials across four condition areas selected to stress-test different parts of the agent:

- **Type 2 Diabetes** — multiple competing drug classes (GLP-1, SGLT2, DPP-4), high contradiction density
- **Non-Small Cell Lung Cancer** — biomarker-stratified outcomes, forces SQL + vector retrieval together
- **Heart Failure** — HFrEF/HFpEF subtypes with genuinely different drug responses
- **Major Depressive Disorder** — high placebo response rates create real, documented contradictions


## Project structure

```
clinicalmind/
├── ingestion/              # Pulls and normalizes ClinicalTrials.gov data
├── agent/
│   ├── graph.py             # LangGraph wiring
│   ├── nodes/                # decomposer, retriever, conflict_detector, synthesizer
│   └── tools/                 # sql_tool.py, vector_tool.py
├── evaluation/              # RAGAS scoring + baseline comparison
├── api/                     # FastAPI app, schemas, metrics
├── monitoring/               # Prometheus config (local), Grafana Cloud setup
├── tests/                    # pytest suite
├── streamlit_app.py          # Demo UI
├── .github/workflows/ci.yml  # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml         # Local dev only
└── requirements.txt
```

## Running locally

```bash
# Clone and install
git clone https://github.com/yourname/clinicalmind.git
cd clinicalmind
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Fill in OPENAI_API_KEY, GROQ_API_KEY, DATABASE_PATH, FAISS_INDEX_PATH

# Run ingestion (one-time, ~10 minutes)
python ingestion/fetch_trials.py
python ingestion/load_sqlite.py
python ingestion/embed_and_index.py

# Run the full stack
docker-compose up --build

# Or run services individually
uvicorn api.main:app --reload --port 8080
streamlit run streamlit_app.py
```

Test the API:

```bash
curl http://localhost:8080/health

curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What Phase 3 GLP-1 trials completed after 2020?"}'
```

## Deployment

Deployed on Google Cloud Run with data hosted on Cloud Storage. Every push to `main` triggers GitHub Actions to run tests, build the Docker image, push to Artifact Registry, and deploy automatically. See `.github/workflows/ci.yml` for the full pipeline.

## License

MIT
