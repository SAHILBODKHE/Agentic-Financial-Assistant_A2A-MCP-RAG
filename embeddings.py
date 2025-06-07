from langchain.embeddings import HuggingFaceEmbeddings

def load_bge_model():
    """
    Loads the BGE-large embedding model wrapped for LangChain compatibility.
    This model will be used with ChromaDB for vector storage and retrieval.
    """
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en",
        model_kwargs={"device": "cpu"},  # change to "cuda" if you have a GPU
        encode_kwargs={"normalize_embeddings": True}
    )
