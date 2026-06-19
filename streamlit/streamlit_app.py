import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8080")

st.set_page_config(page_title="MultiHop Clinical RAG Demo", layout="wide")
st.title("MultiHop Clinical RAG")
st.caption("Multi-hop agentic RAG over 16K+ clinical trials")
st.caption("Target Conditions: Rheumatoid Arthritis, Non-Small Cell Lung Cancer, Type 2 Diabetes, Heart Failure")


example_queries = [
    "What is the most widely used drug for treatment of arthritis in 2026?",
    "Do trials for semaglutide show consistent cardiovascular outcomes?",
    "Which sponsors are running immunotherapy trials for NSCLC with enrollment > 500?",
]

query = st.selectbox("Try an example query:", [""] + example_queries)
custom = st.text_input("Or enter a custom query:")
final_query = custom or query

if st.button("Ask") and final_query:
    with st.spinner("Agent reasoning..."):
        resp = requests.post(f"{API_URL}/query", json={"question": final_query})
        data = resp.json()
        
    st.markdown("### Answer")
    st.write(data["answer"])
    print(f'\n\n--------\n{data['answer']}\n---------\n\n')

    col1, col2, col3 = st.columns(3)
    col1.metric("Confidence", f"{data['confidence_score']:.0%}")
    col2.metric("Latency", f"{data['latency_ms']:.0f}ms")
    col3.metric("Conflicts", "⚠️ Yes" if data["conflicts_detected"] else "✅ None")

    if data["conflicts_detected"]:
        st.warning(f"**Conflicting evidence detected:** {data['conflict_details']}")

    st.markdown("**Citations:** " + ", ".join(data["citations"]))

    if data.get("eval_scores"):
        st.markdown("### Evaluation Scores")
        scores = data["eval_scores"]
        faithfulness = scores["faithfulness"]
        st.progress(
            faithfulness if faithfulness is not None else 0,
            text=f"Faithfulness: {faithfulness:.2f}" if faithfulness is not None else "Faithfulness: N/A"
        )
        ans_relevancy = scores["answer_relevancy"]
        st.progress(
            ans_relevancy if ans_relevancy is not None else 0,
            text=f"Answer Relevancy: {ans_relevancy:.2f}" if ans_relevancy is not None else "Answer Relevancy: N/A"
        )
        # st.progress(scores["faithfulness"], text=f"Faithfulness: {scores['faithfulness']:.2f if value is not None else 'N/A'}")
        # st.progress(scores["answer_relevancy"], text=f"Answer Relevancy: {scores['answer_relevancy']:.2f if scores['answer_relevancy'] is not None else 'N/A'}")
