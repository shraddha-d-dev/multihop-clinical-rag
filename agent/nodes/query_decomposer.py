from __future__ import annotations
from typing import TYPE_CHECKING
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import json, re

if TYPE_CHECKING:
    from agent.graph import AgentState

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.5
)

DECOMPOSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at decomposing complex clinical research questions into simple, atomic sub-queries. Each sub-query should be answerable from a single source. Return ONLY a JSON list of strings.'
    Example: ["What phase 3 diabetes trials completed after 2020?",
        "What HbA1c reductions were reported in these trials?",
        "What were the dropout rates in treatment vs control arms?"
    ]"""),
    ("human", "Decompose this query: {query}")
])


def decompose_node(state: AgentState) -> AgentState:
    chain = DECOMPOSE_PROMPT | llm
    result = chain.invoke({"query": state["original_query"]})

    match = re.search(r'\[.*\]', result.content, re.DOTALL)

    sub_queries = json.loads(match.group() if match else [state["original_query"]])
    return {**state, "sub_queries": sub_queries}