from __future__ import annotations
from typing import TYPE_CHECKING
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import json
from agent.tools.sql_tool import sql_retrieve
from agent.tools.vector_tool import vector_retrieve
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL=os.getenv("LLM_MODEL")

if TYPE_CHECKING:
    from agent.graph import AgentState

llm = ChatGroq(model=LLM_MODEL, temperature=0)

CONFLICT_PROMPT = ChatPromptTemplate.from_messages([
    ("system","""You are a clinical research analyst. Review the retrieved trial results and determine if any trials show conflicting outcomes for the same intervention or question. A conflict exists when:
    - Trials report statistically opposite results on the same endpoint.
    - Trials show meaningfully different effect sizes (>2x differece)
    - One trial shows benefit while another shows harm or no effect.
    
    Return JSON: {{"conflict": true/false, "explanation": "..."}}
    If no conflict, explanation should be "Results are consistent." """),
    ("human", """Original query: {query}
    SQL results: {sql_results}
    Vector results: {vector_results}""")
])

def conflict_detector_node(state: AgentState) -> AgentState:
    chain = CONFLICT_PROMPT | llm

    result = chain.invoke({
            "query": state["original_query"],
            "sql_results": json.dumps(state["sql_results"][:10], indent=2),
            "vector_results": json.dumps(state["vector_results"][:6], indent=2)
    })
    try:
        parsed = json.loads(result.content)
        conflict = parsed.get("conflict", False)
        explanation = parsed.get("explanation", "")
    except:
        conflict = False
        explanation = ""
    return {**state, "conflicts_detected": conflict, "conflict_details": explanation}
    

