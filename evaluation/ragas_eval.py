from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from datasets import Dataset
import sqlite3
from datetime import datetime

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
        
    result = evaluate(dataset, metrics=metrics)
    return {
        "faithfulness": float(result["faithfulness"]),
        "answer_relevancy": float(result["answer_relevancy"]),
        "context_recall": float(result.get("context_recall", -1))
    }

def log_eval(query: str, scores: dict, citations: list, conflict: bool, db_path: str):
    conn = sqlite3.load(db_path)
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

    cursor.execute("INSERT INTO eval_log VALUES(?,?,?,?,?,?,?)",
                datetime.now().isoformat(), 
                query, 
                scores["faithfulness"], 
                scores["answer_relvancy"], 
                scores["context_recall"], 
                len(citations), 
                int(conflict)
    )

    conn.commit()
    conn.close()
