import os

# Get the project root directory (two levels up from this config file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSISTENCE_DIR = os.path.join(PROJECT_ROOT, "persistent_index")

GEMINI_MODEL_NAME = "gemini-2.5-flash"  # Latest Gemini 2.5 Flash model
GEMINI_REASONING_MODEL_NAME = "gemini-2.5-pro" 