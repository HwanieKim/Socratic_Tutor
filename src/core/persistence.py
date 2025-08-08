import os
import asyncio
from dotenv import load_dotenv
import glob
import shutil

from llama_cloud_services import LlamaParse
from llama_index.core.indices import MultiModalVectorStoreIndex
from llama_index.embeddings.voyageai import VoyageEmbedding
from sqlalchemy import true
from . import config

load_dotenv()

# Default directories for backward compatibility
PERSISTENCE_DIR = config.PERSISTENCE_DIR
DATA_DOCUMENTS_DIR = config.DATA_DOCUMENTS_DIR
DATA_IMAGES_DIR = config.DATA_IMAGES_DIR

async def create_index_from_files(file_paths: list = None, output_dir: str = None):
    """
    Creates and persists the vector store index from specified files.
    
    Args:
        file_paths: List of PDF file paths to process. If None, uses default documents directory.
        output_dir: Directory to save the index. If None, uses default persistence directory.
        
    Returns:
        str: Path to the created index directory
        
    Raises:
        ValueError: If no PDF files are provided or found
    """
    print("Creating new index...")
    
    if file_paths is None:
        # Default behavior: scan documents directory
        file_paths = glob.glob(os.path.join(DATA_DOCUMENTS_DIR, "*.pdf"))
    
    if not file_paths:
        raise ValueError("No PDF files provided or found")
    
    # Set output directory
    persist_dir = output_dir or PERSISTENCE_DIR
    
    # Clean existing index if it exists
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
    os.makedirs(persist_dir, exist_ok=True)
    
    # Also create images directory for this index
    images_dir = os.path.join(persist_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    print(f"Processing {len(file_paths)} PDF files...")
    print(f"Files: {[os.path.basename(f) for f in file_paths]}")
    
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
            image_download_dir=images_dir  # Use index-specific images directory
        )
        all_markdown_nodes.extend(markdown_nodes)
        all_image_nodes.extend(image_nodes)

    all_nodes = [*all_markdown_nodes, *all_image_nodes]
    print(f"LlamaParse completed. Found {len(all_markdown_nodes)} text nodes and {len(all_image_nodes)} image nodes in total.")
    
    # embedding model
    embed_model = VoyageEmbedding(
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
    print(f"Saving index to {persist_dir}")
    index.storage_context.persist(persist_dir=persist_dir)
    print("Index created and saved.")
    
    return persist_dir

async def create_index():
    """
    Creates and persists the vector store index from default documents directory.
    
    This function maintains backward compatibility with existing code by using
    default directories for document processing and index storage.
    
    Returns:
        str: Path to the created index directory
    """
    return await create_index_from_files()

if __name__ == "__main__":
    if os.path.exists(PERSISTENCE_DIR):
        print(f"index already exists at {PERSISTENCE_DIR}")
    else:
        asyncio.run(create_index())