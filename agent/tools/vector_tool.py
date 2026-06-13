import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

EMBEDDINGS_MODEL=os.getenv("EMBEDDINGS_MODEL")

def vector_retrieve(query: str, index_path: str, k: int) -> list[dict]: 
    
    embeddings = HuggingFaceEmbeddings(model=EMBEDDINGS_MODEL)
    vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    docs = vectorstore.similarity_search_with_score(query, k)
    
    return [
        {
            "content": doc.page_content, 
            "nct_id": doc.metadata.get("nct_id"),
            "score": float(score)
        }
        for doc, score in docs
    ]
