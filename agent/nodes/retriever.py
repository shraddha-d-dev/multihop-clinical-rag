from __future__ import annotations
from typing import TYPE_CHECKING
import os
from agent.tools.sql_tool import sql_retrieve
from agent.tools.vector_tool import vector_retrieve
from dotenv import load_dotenv

if TYPE_CHECKING:
    from agent.graph import AgentState

DB_PATH = os.getenv("DB_PATH")
INDEX_PATH = os.getenv("INDEX_PATH")
VECTOR_K   = 3


def retrieve_for_subquery(sub_query: str) -> dict:
    """
    Runs SQL and vector retrieval sequentially for a single sub-query.
    """
    # No executor.submit() — just call the functions directly
    sql_rows      = sql_retrieve(sub_query, DB_PATH)
    vector_chunks = vector_retrieve(sub_query, INDEX_PATH, VECTOR_K)

    return {
        "sub_query":      sub_query,
        "sql_rows":       sql_rows,
        "vector_chunks":  vector_chunks,
    }


def retriever_node(state: AgentState) -> AgentState:
    """
    LangGraph node.
    Reads:  state['sub_queries'], state['original_query']
    Writes: state['sql_results'], state['vector_results']
    """
    sub_queries = state.get("sub_queries") or [state.get("original_query", "")]

    all_sql_rows      = []
    all_vector_chunks = []

    # Run all sub-queries sequentially using a standard for-loop
    for sq in sub_queries:
        try:
            result = retrieve_for_subquery(sq)
            all_sql_rows.extend(result["sql_rows"])
            all_vector_chunks.extend(result["vector_chunks"])
        except Exception as e:
            # Log but don't crash — partial results are still useful
            print(f"[retriever] sub-query failed: {sq} — {e}")

    # Deduplicate SQL rows by nct_id — first occurrence wins
    seen     = set()
    deduped  = []
    for row in all_sql_rows:
        nct_id = row.get("nct_id")
        if nct_id and nct_id not in seen:
            seen.add(nct_id)
            deduped.append(row)
        elif not nct_id:
            # Keep error rows so conflict detector can see what failed
            deduped.append(row)

    # Sort vector chunks by score ascending (lower L2 = more similar)
    all_vector_chunks.sort(key=lambda x: x.get("score", 999))

    return {
        **state,
        "sql_results":    deduped[:20],
        "vector_results": all_vector_chunks[:12],
    }