import os

# Get the project root directory (two levels up from this config file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSISTENCE_DIR = os.path.join(PROJECT_ROOT, "persistent_index")

# Data directories
DATA_DOCUMENTS_DIR = os.path.join(PROJECT_ROOT, "data", "documents")
DATA_IMAGES_DIR = os.path.join(PROJECT_ROOT, "data", "images")

# Railway Volume 경로 (영구 저장소)
RAILWAY_VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", os.path.join(PROJECT_ROOT, "railway_data"))
USER_UPLOADS_DIR = os.path.join(RAILWAY_VOLUME_PATH, "user_uploads")
USER_INDEXES_DIR = os.path.join(RAILWAY_VOLUME_PATH, "user_indexes")

# 디렉토리 생성
os.makedirs(USER_UPLOADS_DIR, exist_ok=True)
os.makedirs(USER_INDEXES_DIR, exist_ok=True)
os.makedirs(RAILWAY_VOLUME_PATH, exist_ok=True)

# Model configurations
GEMINI_MODEL_NAME = "gemini-2.5-flash"  # Latest Gemini 2.5 Flash model
GEMINI_REASONING_MODEL_NAME = "gemini-2.5-pro"

# Embedding model
VOYAGE_EMBEDDING_MODEL = "voyage-multimodal-3"