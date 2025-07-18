import os
import asyncio
from dotenv import load_dotenv
import glob

from llama_cloud_services import LlamaParse
from llama_index.core.indices import MultiModalVectorStoreIndex
from llama_index.embeddings.voyageai import VoyageEmbedding
from sqlalchemy import true
load_dotenv()

# Ensure the necessary directories exist
PERSISTENCE_DIR = "./persistent_index"
DATA_DOCUMENTS_DIR = "./data/documents"
DATA_IMAGES_DIR = "./data/images"

async def create_index():
    """Creates and persists the vector store index."""
    print("Creating new index...")

    # todo: add other file types if needed
    # only pdf files in the documents directory can be processed
    file_paths = glob.glob(os.path.join(DATA_DOCUMENTS_DIR, "*.pdf"))

    parser = LlamaParse(
        api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
        result_type="markdown",
        take_screenshot=True,
        show_progress=True,
        auto_mode=True,
        
    )
    result = await parser.aparse(file_path=file_paths)

    all_markdown_nodes = []
    all_image_nodes = []
    
    for result_item in result:
        markdown_nodes = await result_item.aget_markdown_nodes(
            split_by_page=True,
        )
        image_nodes = await result_item.aget_image_nodes(
            include_screenshot_images=True,
            include_object_images=False,
            image_download_dir=DATA_IMAGES_DIR
    )
        all_markdown_nodes.extend(markdown_nodes)
        all_image_nodes.extend(image_nodes)

    all_nodes = [*all_markdown_nodes, *all_image_nodes]
    print(f"LlamaParse completed. Found {len(all_markdown_nodes)} text nodes and {len(all_image_nodes)} image nodes in total.")
    
    # embedding model
    embed_model=VoyageEmbedding(
        model_name="voyage-multimodal-3",
        voyage_api_key=os.getenv("VOYAGE_API_KEY"),
        truncation=True
    )

    # vector store index
    index = MultiModalVectorStoreIndex(
        nodes=all_nodes,
        embed_model=embed_model,
        image_embed_model=embed_model,
        show_progress=True
    )

    # persistence context
    print(f"saving index to {PERSISTENCE_DIR}")
    index.storage_context.persist(persist_dir=PERSISTENCE_DIR)
    print("Index created and saved.")

if __name__ == "__main__":
    if os.path.exists(PERSISTENCE_DIR):
        print(f"index already exists at {PERSISTENCE_DIR}")
    else:
        asyncio.run(create_index())





