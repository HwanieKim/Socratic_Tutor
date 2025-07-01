import os
from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
load_dotenv()

PERSISTENCE_DIR = "./persistent_index"
DATA_DIR = "./data"
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"

if os.path.exists(PERSISTENCE_DIR):
    print(f"index already exists at {PERSISTENCE_DIR}")
else: 
    # embedding model
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
    # loading documents
    reader = SimpleDirectoryReader(input_dir=DATA_DIR)
    documents = reader.load_data()

    # vector store index
    index = VectorStoreIndex.from_documents(
    documents,
    embed_model=embed_model,
    show_progress=True
    )

    # persistence context
    print(f"saving index to {PERSISTENCE_DIR}")
    index.storage_context.persist(
    persist_dir=PERSISTENCE_DIR
)





