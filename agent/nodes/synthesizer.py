from __future__ import annotations
from typing import TYPE_CHECKING
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import json
from dotenv import load_dotenv

load_dotenv()

if TYPE_CHECKING:
    from agent.graph import AgentState

LLM_MODEL = os.getenv("LLM_MODEL")

llm = ChatGroq(model=LLM_MODEL, temperature=0)

SYNTHESIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a clinical research assistant. Synthesize a clear, accurate answer from the retrieved evidence. Rules:
    - Cite every claim with the NCT ID of the source trial.
    - If conflicts were detected, explicitly state the disagreement.
    - Be precise with numbers; do not extrapolate beyond the data.
    - End with a list of cited NCT IDs.

    Return JSON: {{"answer": "...", "citations": ["NCT...", "..."], "confidence": 0.0-1.0}}
    """),
    ("human", """Query: {query}, 
    Evidence: {evidence},
    Conflicts detected: {conflict}
    Conflict details: {conflict_details} """)
])

def synthesizer_node(state: AgentState) -> AgentState:
    evidence = {
        "sql": state["sql_results"][:10],
        "vector": state["vector_results"][:6]
    }
    chain = SYNTHESIZE_PROMPT | llm
    result = chain.invoke({
        "query": state["original_query"],
        "evidence": json.dumps(evidence, indent=2),
        "conflict": state["conflicts_detected"],
        "conflict_details": state["conflict_details"]
    })

    try:
        parsed = json.loads(result.content)
    except:
        parsed = {"answer": result.content, "citations": [], "confidence": 0.5}
    return {**state, 
            "final_answer": parsed.get("answer", ""),
            "citations": parsed.get("citations", []),
            "confience_score": parsed.get("confidence", 0.5)}
