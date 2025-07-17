import os

# Get the project root directory (two levels up from this config file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSISTENCE_DIR = os.path.join(PROJECT_ROOT, "persistent_index")

# Data directories
DATA_DOCUMENTS_DIR = os.path.join(PROJECT_ROOT, "data", "documents")
DATA_IMAGES_DIR = os.path.join(PROJECT_ROOT, "data", "images")

# Model configurations
GEMINI_MODEL_NAME = "gemini-2.5-flash"  # Latest Gemini 2.5 Flash model
GEMINI_REASONING_MODEL_NAME = "gemini-2.5-pro"

# Embedding model
VOYAGE_EMBEDDING_MODEL = "voyage-multimodal-3"