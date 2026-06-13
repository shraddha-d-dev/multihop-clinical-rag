import os
from fastapi import FastAPI
from api.schemas import QueryRequest, QueryResponse
from prometheus_client import Counter, Histogram, generate_latest
from evaluation.ragas_eval import evaluate_response, log_eval
from fastapi.responses import PlainTextResponse
import time
from agent.graph import agent
from dotenv import load_dotenv

LOG_DB_PATH = os.getenv("LOG_DB_PATH")

app = FastAPI(title="MultiHop Clinical RAG", version="1.0.0")

REQUEST_COUNT = Counter("api_requests_total", "Total requests")
LATENCY = Histogram("api_latency_seconds", "Request Latency")
HALLUCINATION_RATE = Counter("api_conflicts_total", "Conflict flags")

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    REQUEST_COUNT.inc()
    start = time.time()

    initial_state = {
        "original_query": request.question,
        "sub_queries": [], 
        "sql_results": [],
        "vector_results": [], 
        "conflicts_detected": False,
        "conflict_details": "", 
        "citations": [], 
        "confidence_score": 0.0
    }
    state = agent.invoke(initial_state)

    latency_ms = (time.time() - start) * 1000
    LATENCY.observe(latency_ms / 1000)

    if state["conflicts_detected"]:
        HALLUCINATION_RATE.inc()

    eval_scores = None
    if request.include_eval:
        contexts = [r.get("content", "") for r in state["vector_results"][:4]]
        eval_scores = evaluate_response(request.question, state["final_answer"], contexts)
        log_eval(request.question, eval_scores, state["citations"], state["conflicts_detected"], LOG_DB_PATH)

    return QueryResponse(
        answer=state["final_answer"], 
        citations=state["citations"], 
        confidence_score=state["confidence_score"],
        conflicts_detected=state["conflicts_detected"],
        conflict_details=state["conflict_details"],
        eval_scores=eval_scores,
        latency_ms=round(latency_ms, 1)
    )

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest())

@app.get("/health")
def health():
    return {"status": "ok"}