# PolyGlot Socratic Tutor

An AI-powered tutoring system that uses Socratic dialogue methodology to help students learn from uploaded documents. The system employs a sophisticated multi-stage pipeline with intelligent scaffolding to guide students through complex topics.

## 🎯 Features

-   **Socratic Dialogue**: Guides students to discover answers through strategic questioning
-   **Multi-Modal RAG**: Processes both text and images from PDF documents using LlamaIndex
-   **Intelligent Scaffolding**: 4-level progressive support system when students struggle
-   **Topic Relevance Filtering**: Keeps conversations focused on course materials
-   **Production-Ready**: Rate limiting, error handling, and conversation metrics
-   **Real-time Web UI**: Clean Gradio interface with lazy index creation

## 🏗️ System Architecture (Modular Design)

### Core Components

The system follows a **modular architecture** where each component has a specific responsibility:

1. **TutorEngine** (`src/core/tutor_engine.py`): Main orchestrator following SOAR pattern
2. **IntentClassifier** (`src/core/intent_classifier.py`): Stage 0 & 0b intent classification
3. **RAGRetriever** (`src/core/rag_retriever.py`): Stage 1 hybrid retrieval and expert reasoning
4. **AnswerEvaluator** (`src/core/answer_evaluator.py`): Stage 1b student answer evaluation
5. **DialogueGenerator** (`src/core/dialogue_generator.py`): Stage 2 Socratic dialogue generation
6. **ScaffoldingSystem** (`src/core/scaffolding_system.py`): Progressive support mechanism
7. **MemoryManager** (`src/core/memory_manager.py`): Conversation memory and context caching
8. **ProductionTutorEngine** (`src/core/production_enhancements.py`): Production wrapper with safety features

### Pipeline Stages

-   **Stage 0**: Intent classification (new question vs. follow-up)
-   **Stage 0b**: Follow-up type classification (answer attempt vs. meta-question)
-   **Stage 1**: Expert reasoning and knowledge retrieval from documents
-   **Stage 1b**: Student answer evaluation and feedback
-   **Stage 2**: Socratic dialogue generation with contextual guidance

### Scaffolding Levels

When students struggle, the system provides progressive support:

1. **Level 1**: Focused hints and clarification
2. **Level 2**: Helpful analogies and examples
3. **Level 3**: Multiple choice questions
4. **Level 4**: Direct answers with explanations

## 📋 Prerequisites

-   Python 3.8+
-   **Google API Key** (for Gemini 2.5 models)
-   **Voyage AI API Key** (for multimodal embeddings)
-   **LlamaCloud API Key** (for document parsing)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd example_rag

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
VOYAGE_API_KEY=your_voyage_api_key_here
LLAMA_CLOUD_API_KEY=your_llamacloud_api_key_here
```

### 3. Prepare Documents

```bash
# Create data directory
mkdir -p data/documents

# Add your PDF files to data/documents/
# The system will extract text and images automatically
```

### 4. Launch the Application

```bash
# Production UI (recommended) - with built-in index creation
python src/ui/gradio_ui_production.py
```

The application will start on `http://127.0.0.1:7862`

### 5. Initialize the System (Enhanced Step-by-Step Guide)

1. Open your browser to `http://127.0.0.1:7862`

2. **Step 1: Upload Documents** 📝

    - The chat interface will be **disabled** until you complete this step
    - Upload your PDF documents using the file upload area
    - You'll see a status update when upload is successful
    - Chat placeholder will show: _"Please complete Step 1: Upload your documents first"_

3. **Step 2: Create Index** ⚙️

    - After uploading, the "Create Index" button will appear
    - Click it to process your documents (may take several minutes)
    - Chat remains **disabled** with message: _"Please complete Step 2: Create index from your documents"_
    - Wait for the "Index created successfully" message

4. **Step 3: Start Tutoring** ✅
    - Once both steps are complete, the chat interface will be **enabled**
    - Chat placeholder changes to: _"Ready! Ask me anything about your documents..."_
    - You can now ask questions and engage with your AI tutor

> **Note**: The system enforces this step-by-step process to ensure proper setup. You cannot access the chat until both document upload and index creation are completed.

    - Click "2. Initialize Engine" to start the tutor

3. **Subsequent Uses**:
    - If index exists, just click "2. Initialize Engine"
4. Begin asking questions about your documents!

## 📁 Project Structure

```
example_rag/
├── src/
│   ├── core/
│   │   ├── __init__.py              # Package initialization
│   │   ├── tutor_engine.py          # 🎯 Main orchestrator (SOAR pattern)
│   │   ├── intent_classifier.py     # 🧠 Stage 0 & 0b logic
│   │   ├── rag_retriever.py         # 🔍 Stage 1 RAG and reasoning
│   │   ├── answer_evaluator.py      # 📊 Stage 1b evaluation logic
│   │   ├── dialogue_generator.py    # 💬 Stage 2 Socratic dialogue
│   │   ├── scaffolding_system.py    # 🏗️ Progressive support system
│   │   ├── memory_manager.py        # 🧠 Memory and context management
│   │   ├── production_enhancements.py # 🛡️ Production features
│   │   ├── models.py                # 📋 Pydantic data models
│   │   ├── prompts_template.py      # 📝 LLM prompt templates
│   │   ├── config.py                # ⚙️ Configuration settings
│   │   └── persistence.py           # 💾 Index creation and storage
│   └── ui/
│       ├── gradio_ui_production.py  # 🌐 Production web interface
│       └── gradio_ui_fast.py        # ⚡ Fast development interface
├── data/
│   ├── documents/                   # 📚 PDF documents for processing
│   └── images/                      # 🖼️ Extracted images from PDFs
├── persistent_index/                # 🗂️ Vector index storage
├── requirements.txt                 # 📦 Python dependencies
├── test_integration.py              # 🧪 Module integration tests
└── README.md                        # 📖 Documentation
│   │   ├── persistence.py           # Index creation and management
│   │   └── config.py                # System configuration
│   └── ui/
│       ├── __init__.py              # UI package
│       └── gradio_ui_production.py  # Production web interface
├── data/
│   ├── documents/                   # PDF files (user provided)
│   └── images/                      # Extracted images (auto-generated)
├── persistent_index/                # Vector index (auto-generated)
├── requirements.txt
├── README.md
└── .env                            # API keys (create this)
```

## 🎓 How It Works

### Student Learning Journey

1. **Question**: Student asks about course materials
2. **Retrieval**: System searches through uploaded documents
3. **Expert Analysis**: AI generates comprehensive reasoning
4. **Socratic Response**: Tutor guides student with strategic questions
5. **Progressive Support**: If student struggles, system escalates help

### Example Interaction

```
Student: "What is pretotyping?"

Tutor: "Great question! Based on the text, how would you define
pretotyping in your own words? Feel free to use the definitions
on page 37 as a starting point."

Student: "I don't get it"

Tutor: "No problem! Let me try a different approach. Imagine
you're a chef who wants to introduce a new dish. Instead of
buying all ingredients in bulk, you first make a tiny sample
to test if customers like it. How does this relate to the
concept of pretotyping?"

Student: "Still confused"

Tutor: "Let me give you a multiple choice question:
What is the main purpose of pretotyping?
a) To build a complete product
b) To test if people want your idea before building it
c) To save money on materials
d) To impress investors"
```

## 🛠️ Configuration

### Model Settings (`src/core/config.py`)

```python
# AI Models
GEMINI_MODEL_NAME = "gemini-2.5-flash"           # For conversations
GEMINI_REASONING_MODEL_NAME = "gemini-2.5-pro"   # For analysis
VOYAGE_EMBEDDING_MODEL = "voyage-multimodal-3"   # For embeddings

# Data Paths
DATA_DOCUMENTS_DIR = "data/documents"
DATA_IMAGES_DIR = "data/images"
PERSISTENCE_DIR = "persistent_index"
```

### Production Features

-   **Lazy Index Creation**: Create index through web UI when needed
-   **Rate Limiting**: Prevents API quota exhaustion
-   **Input Validation**: Length limits and content filtering
-   **Error Handling**: Graceful degradation for API failures
-   **Conversation Metrics**: Usage tracking and analytics
-   **Multi-user Support**: Isolated conversations per user

## 🔧 API Reference

### Basic Usage

```python
from src.core.tutor_engine import TutorEngine

# Initialize engine (requires existing index)
engine = TutorEngine()

# Get response
response = engine.get_guidance("What is sustainable design?")
print(response)

# Reset conversation
engine.reset()
```

### Production Usage

```python
from src.core.tutor_engine import TutorEngine
from src.core.production_enhancements import ProductionTutorEngine

# Enhanced engine with safety features
base_engine = TutorEngine()
prod_engine = ProductionTutorEngine(base_engine)

# Get response with rate limiting
response = prod_engine.get_guidance("Question here", user_id="student123")

# Get conversation metrics
metrics = prod_engine.get_metrics()
```

### Index Creation

```python
from src.core.persistence import create_index
import asyncio

# Create index programmatically
asyncio.run(create_index())
```

## 🚨 Troubleshooting

### Common Issues

1. **"No index found" error**:

    - Use the web UI to create index: Click "1. Create Index"
    - Ensure PDF files are in `data/documents/` directory

2. **Index creation fails**:

    - Check API keys in `.env` file
    - Verify PDF files exist in `data/documents/`
    - Check internet connection for API calls

3. **Engine initialization fails**:
    - Ensure index was created successfully
    - Check for required index files in `persistent_index/`

### System Requirements

-   **Memory**: 4GB+ RAM recommended for document processing
-   **Storage**: 1GB+ for index files (varies by document size)
-   **Network**: Stable internet for API calls during index creation

**Version**: 1.0.0  
**Last Updated**: July 2025  
**Python Version**: 3.8+  
**License**: MIT
