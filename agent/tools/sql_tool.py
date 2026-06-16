import os
import sqlite3
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL=os.getenv("LLM_MODEL")

def nl_to_sql(query: str, schema: str) -> str:
    llm = ChatGroq(
        model = LLM_MODEL,
        temperature = 0
    )
    prompt = f"""Convert this natural language query into SQlite SQL.
    Schema: {schema}
    Query: {query}
    Return only the executable SQL query with proper syntax without any addtional characters or explanation."""
    return llm.invoke(prompt).content.strip()

def sql_retrieve(query: str, db_path: str) -> list[dict]:
    schema = """CREATE TABLE IF NOT EXISTS trials (
            nct_id TEXT PRIMARY KEY,
            title TEXT,
            conditions TEXT,
            phases TEXT,
            enrollment_count INTEGER,
            start_date TEXT,
            completion_date TEXT,
            lead_sponsor TEXT
        )"""
    sql_query = nl_to_sql(query, schema)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        rows = cursor.execute(sql_query).fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        return [{"error": str(e), "sql query": sql_query}]
    finally:
        conn.close()
