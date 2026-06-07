from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from agent.nodes.query_decomposer import decompose_node
from agent.nodes.retriever import retriever_node 
from agent.nodes.conflict_detector import conflict_detector_node
from agent.nodes.synthesizer import synthesizer_node

class AgentState(TypedDict):
    original_query: str
    sub_queries: List[str]
    sql_results: List[dict]
    vector_results: List[dict]
    conflicts_detected: bool
    conflict_details: Optional[str]
    final_answer: str
    citations: List[str]
    confidence_score: float

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("decompose", decompose_node)
    graph.add_node("retrieve", retriever_node)
    graph.add_node("conflict_detector", conflict_detector_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.set_entry_point("decompose")
    graph.add_edge("decompose", "retrieve")
    graph.add_edge("retrieve", "conflict_detector")
    graph.add_edge("conflict_detector", "synthesizer")
    
    return graph.compile()

agent = build_graph()