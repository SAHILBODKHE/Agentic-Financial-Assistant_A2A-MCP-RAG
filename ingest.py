import os
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from embeddings import load_bge_model

def ingest_documents():
    documents = []
    for file in os.listdir("data"):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join("data", file))
            documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=100)
    texts = splitter.split_documents(documents)

    bge_model = load_bge_model()
    db = Chroma.from_documents(
        documents=texts,
        embedding=bge_model,
        persist_directory="db"
    )
    db.persist()
    print("✅ Ingestion complete.")

if __name__ == "__main__":
    ingest_documents()
