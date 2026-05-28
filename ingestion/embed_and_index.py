import torch
import faiss
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.faiss import FAISS

def build_vector_index(studies, embeddings, index_path, batch_size):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        separators=["\n\n", "\n", ". "]
    )

    
    documents = []

    for idx, study in enumerate(studies):
        protocol_mod = study.get('protocolSection', {})
        id_mod = protocol_mod.get('identificationModule', {})
        desc_mod = protocol_mod.get('descriptionModule', {})
        intervention_mod = protocol_mod.get('armsInterventionsModule', {})
        outcome_mod = protocol_mod.get('outcomesModule', {})
        eligibility_mod = protocol_mod.get('eligibilityModule', {})
        results_mod = protocol_mod.get('resultsSection', {})

        text_fields = [
            desc_mod.get('briefSummary',''),
            desc_mod.get('detailedDescription', ''),
            json.dumps(intervention_mod.get('interventions', [])),
            json.dumps(outcome_mod.get('primaryOutcomes', [])),
            eligibility_mod.get('eligibilityCriteria', ''),
            json.dumps(results_mod)
        ]

        full_text = '\n\n'.join(filter(None, text_fields))

        chunks = splitter.split_text(full_text)

        for chunk in chunks:
            documents.append(
                Document(
                    page_content = chunk,
                    metadata = {
                        "nct_id": id_mod.get('nctId'),
                        "source": "clinicaltrials.gov"
                    },
                )
            )
        print(f"Processed study #{idx+1} with {len(chunks)} chunks")

    vector_store = FAISS.from_documents([documents[0]], embeddings)
    for i in range(1, len(documents), batch_size):
        batch = documents[i: i + batch_size]
        vector_store.add_documents(batch)
        print(f"Indexed chunks {i} to {i + len(batch)}")

    
    vector_store.save_local(index_path)

    print(f'Indexed {len(documents)} chunks from {len(studies)} trials')


if __name__ == '__main__':

    with open('data/trial_data.json', 'r') as f:
        studies = json.load(f)
    index_path = 'data/faiss_index'
    batch_size = 50
    embeddings = HuggingFaceEmbeddings(model="BAAI/bge-small-en-v1.5")

    
    build_vector_index(studies, embeddings, index_path, batch_size)



    db = FAISS.load_local(
    folder_path=index_path, 
    embeddings=embeddings,
    allow_dangerous_deserialization=True  # Required to safely unpack the local index
)
    query = "What do you know about treatments for Heart Failure?"

    matching_docs = db.similarity_search(query, k=3)

    for i, doc in enumerate(matching_docs):
        print(f"Result {i+1}:")
        print(doc.page_content)
        print("-" * 20)