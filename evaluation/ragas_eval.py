import os
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset
import sqlite3
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv 

LLM_MODEL = os.getenv("LLM_MODEL")
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL")

llm = ChatGroq(model=LLM_MODEL, temperature=0)
evaluator_llm = LangchainLLMWrapper(llm)

hf_embeddings = HuggingFaceEmbeddings(model_name = EMBEDDINGS_MODEL)
evaluator_embeddings = LangchainEmbeddingsWrapper(hf_embeddings)

def evaluate_response(query: str, answer: str, contexts: list[str], ground_truth: str = "") -> dict:
    data = {
        "question": [query],
        "answer": [answer],
        "contexts": [contexts],
        "ground_truth": [ground_truth] if ground_truth else [""]
    }

    dataset = Dataset.from_dict(data)
    metrics = [faithfulness, answer_relevancy]
    if ground_truth:
        metrics.append(context_recall)
        
    result = evaluate(
        dataset, 
        metrics=metrics, 
        llm=evaluator_llm, 
        embeddings=evaluator_embeddings
    )

    scores = result.scores[0]

    # print(f'========\n{scores}\n==========')

    return {
        "faithfulness": float(scores.get("faithfulness", float('nan'))),
        "answer_relevancy": float(scores.get("answer_relevancy", float('nan'))),
        "context_recall": float(scores.get("context_recall", float('nan')))
    }

def log_eval(query: str, scores: dict, citations: list, conflict: bool, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS eval_log (
                timestamp TEXT,
                query TEXT, 
                faithfulness REAL,
                answer_relevancy REAL,
                context_recall REAL,
                num_citations INTEGER,
                conflict_detected INTEGER
    )""")

    # print('\n\n=====================\n\n')
    # print(type(query), query)
    # print(type(scores["faithfulness"]), scores["faithfulness"]), 
    # print(type(scores["answer_relevancy"]), scores["answer_relevancy"]), 
    # print(type(scores["context_recall"]), scores["context_recall"]), 
    # print(type(len(citations)), len(citations)), 
    # print(type(int(conflict)), int(conflict))
    # print('\n\n=====================\n\n')

    cursor.execute("INSERT INTO eval_log VALUES(?,?,?,?,?,?,?)",
                (datetime.now().isoformat(), 
                query, 
                scores["faithfulness"], 
                scores["answer_relevancy"], 
                scores["context_recall"], 
                len(citations), 
                int(conflict))
    )

    conn.commit()
    conn.close()
