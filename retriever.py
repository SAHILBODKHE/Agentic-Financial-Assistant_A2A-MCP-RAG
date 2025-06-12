from langchain_community.vectorstores import Chroma
from embeddings import load_bge_model

def get_relevant_documents(query, k=3):
    model = load_bge_model()
    db = Chroma(persist_directory="db", embedding_function=model)
    return db.similarity_search(query, k=k)
