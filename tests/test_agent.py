import pytest
from agent.graph import agent

TEST_QUERIES = [
    "What Phase 3 trials for Type 2 Diabetes completed after 2021?",
    "Which GLP-1 trials reported HbA1c reductions greater than 1%?",
    "Do trials for semaglutide show consistent cardiovascular outcomes?",
]

def test_agent_returns_answer():
    state = agent.invoke({
        "original_query": TEST_QUERIES[0],
        "sub_queries": [],
        "sql_results": [], 
        "vector_results": [],
        "conflicts_detected": False, 
        "conflict_details": "",
        "final_answer": "", 
        "citations": [], 
        "confidence_score": 0.0
    })
    assert state["final_answer"] != ""
    assert isinstance(state["citations"], list)
    assert 0.0 <= state["confidence_score"] <= 1.0

def test_conflict_detection_on_known_pair():
    pass