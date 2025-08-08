# 🎓 RAG Socratic Tutor - AI-Powered Learning Assistant

An intelligent tutoring system that uses Retrieval-Augmented Generation (RAG) and Socratic questioning methodology to provide personalized learning experiences from your PDF documents.

## 🌟 Features

### 🧠 Intelligent Tutoring System
- **Socratic Questioning**: Guides learning through strategic questions rather than direct answers
- **Multidimensional Assessment**: Evaluates answers across conceptual accuracy, reasoning coherence, evidence utilization, and conceptual integration
- **Adaptive Scaffolding**: Provides personalized support based on learning level and progress
- **Intent Classification**: Distinguishes between new questions, follow-ups, and meta-questions

### 📚 Advanced RAG Implementation
- **Hybrid Retrieval**: Combines vector search with BM25 for optimal document retrieval
- **Expert Reasoning**: Generates structured reasoning triplets (Question → Reasoning Chain → Answer)
- **Context-Aware Responses**: Maintains conversation memory and context caching
- **Multi-Modal Support**: Handles both text and image content from PDFs

### 🌐 Multi-Language Support
- **Supported Languages**: English, Italian, Spanish
- **Dynamic Language Switching**: Change language without losing session state
- **Localized UI**: Complete interface translation including error messages and tutorials

### 🚀 Production-Ready Features
- **Railway Deployment**: Optimized for Railway platform with PostgreSQL integration
- **Multi-User Sessions**: Concurrent user support with session isolation
- **File Management**: Staged upload system with duplicate detection
- **Database Integration**: Persistent storage for documents, indexes, and learning progress
- **Rate Limiting**: Built-in protection against abuse
- **Enhanced Logging**: Comprehensive monitoring and debugging capabilities

## 🏗️ System Architecture

### Core Components

```
src/
├── core/                          # Core business logic
│   ├── tutor_engine.py           # Main orchestrator (SOAR pattern)
│   ├── models.py                 # Pydantic data models
│   ├── intent_classifier.py     # Question intent classification
│   ├── rag_retriever.py         # Hybrid RAG retrieval system
│   ├── answer_evaluator.py      # Multi-dimensional answer evaluation
│   ├── dialogue_generator.py    # Socratic dialogue generation
│   ├── scaffolding_system.py    # Adaptive learning support
│   ├── memory_manager.py        # Conversation memory management
│   ├── database_manager.py      # PostgreSQL database operations
│   ├── production_enhancements.py # Production features
│   ├── persistence.py           # Index creation and storage
│   ├── i18n.py                  # Internationalization
│   └── config.py               # Configuration management
├── ui/                           # User interfaces
│   ├── gradio_ui_railway.py    # Production Railway UI
│   └── gradio_ui_production.py # Alternative production UI
└── prompts/                     # LLM prompt templates
    └── prompts_template.py
```

### SOAR Pattern Implementation
The system follows the **State, Operator, And, Result** pattern:

1. **State**: Current learning context and session state
2. **Operator**: Specialized modules (RAG, Evaluator, Scaffolding, etc.)
3. **And**: Coordination logic in TutorEngine
4. **Result**: Generated tutoring responses and learning insights

## 🛠️ Technology Stack

- **Backend**: Python 3.8+, FastAPI, LlamaIndex
- **Frontend**: Gradio (Web UI)
- **Database**: PostgreSQL (Railway)
- **LLM**: Google Gemini (via GoogleGenAI)
- **Embeddings**: Voyage AI
- **File Processing**: LlamaParse (PDF processing)
- **Deployment**: Railway platform

## 📦 Installation

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/rag-socratic-tutor.git
cd rag-socratic-tutor
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment setup**
Create a `.env` file in the root directory:
```env
# Required API Keys
GOOGLE_API_KEY=your_google_api_key
VOYAGE_API_KEY=your_voyage_api_key
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key

# Database Configuration (Railway PostgreSQL)
DATABASE_URL=postgresql://username:password@host:port/database

# Railway Configuration
RAILWAY_VOLUME_MOUNT_PATH=/app/data
```

4. **Initialize database**
```bash
python -c "from src.core.database_manager import DatabaseManager; DatabaseManager()._init_tables()"
```

5. **Run the application**
```bash
python src/ui/gradio_ui_railway.py
```

### Railway Deployment

1. **Connect your GitHub repository to Railway**
2. **Add environment variables** in Railway dashboard
3. **Deploy** - Railway will automatically detect and build the application

Required Railway Environment Variables:
- `GOOGLE_API_KEY`
- `VOYAGE_API_KEY` 
- `LLAMA_CLOUD_API_KEY`
- `DATABASE_URL` (automatically provided by Railway PostgreSQL)
- `RAILWAY_VOLUME_MOUNT_PATH` (automatically set)

## 🎯 Usage Guide

### Getting Started

1. **Upload Documents**
   - Upload PDF files using the drag-and-drop interface
   - System checks for duplicate files and existing indexes
   - Files are staged for processing

2. **Create Index**
   - Click "Create Index" to process uploaded documents
   - System creates a searchable vector index
   - Progress is shown with real-time updates

3. **Start Learning**
   - Ask questions about your documents
   - Receive Socratic-style guidance
   - Get personalized scaffolding based on your responses

### Advanced Features

#### Multi-User Sessions
```python
# Each user gets isolated sessions
session_engine = TutorEngine(session_id="user_123", language="en")
await session_engine.initialize_engine()
```

#### Custom Learning Levels
The system adapts to 5 learning levels:
- **L1**: Basic Recognition
- **L2**: Structured Comprehension  
- **L3**: Applied Analysis
- **L4**: Evaluative Synthesis
- **L5**: Creative Integration

#### Scaffolding Strategies
- Multiple choice questions
- Problem breakdown
- Socratic questioning
- Evidence-based prompting
- Metacognitive reflection

## 🔧 Configuration

### Model Configuration
```python
# src/core/config.py
EMBEDDING_MODEL = "voyage-3"
LLM_MODEL = "gemini-2.5-pro"
EMBEDDING_DIMENSIONS = 1024
MAX_TOKENS = 8192
```

### Database Schema
The system creates these tables automatically:
- `uploaded_documents`: Document metadata
- `document_indexes`: Index information
- `user_sessions`: Session tracking
- `learning_evaluations`: Performance data
- `session_interactions`: Conversation history

## 🧪 Testing

### Run Tests
```bash
# Core functionality tests
python -m pytest tests/test_core.py

# UI integration tests  
python -m pytest tests/test_ui.py

# Database tests
python -m pytest tests/test_database.py
```

### Production Features Test
```bash
python src/core/production_enhancements.py
```

## 📊 Monitoring & Analytics

### Learning Insights Dashboard
- Current learning level and progression
- Performance trends and streaks
- Session duration and interaction count
- Multidimensional score analysis

### System Metrics
- Rate limiting status
- Conversation quality metrics
- Database performance
- File processing statistics

## 🌍 Internationalization

### Adding New Languages

1. **Update language constants**
```python
# src/core/i18n.py
SUPPORTED_LANGUAGES = ["en", "it"]
```

2. **Add translations**
```python
UI_TEXTS = {
    "your_language": {
        "app_title": "Your Translation",
        # ... add all required keys
    }
}
```

3. **Test language switching**
```python
from src.core.i18n import get_ui_text
text = get_ui_text("app_title", "your_language")
```

## 🚨 Troubleshooting

### Common Issues

**Index Creation Fails**
- Check PDF file format and size
- Verify LlamaParse API key
- Ensure sufficient disk space

**Database Connection Issues**
- Verify DATABASE_URL format
- Check Railway PostgreSQL service status
- Review connection pooling settings

**Memory Issues**
- Adjust token limits in config
- Clear conversation history
- Restart session

**API Rate Limits**
- Check API key quotas
- Implement exponential backoff
- Use rate limiting features

## 📝 API Reference

### Core Classes

#### TutorEngine
```python
class TutorEngine:
    async def process_user_input(self, user_input: str) -> AsyncGenerator[str, None]
    async def create_user_index(self) -> AsyncGenerator[Dict, None]
    def upload_files(self, files) -> str
    async def load_existing_index(self, index_id: str) -> Dict
```

#### Models
```python
class ReasoningTriplet(BaseModel):
    question: str
    reasoning_chain: str
    answer: str

class EnhancedAnswerEvaluation(BaseModel):
    scores: MultidimensionalScores
    overall_performance: str
    feedback: str
    suggestions: List[str]
```



## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LlamaIndex**: For the RAG framework
- **Railway**: For deployment platform
- **Google**: For Gemini API
- **Voyage AI**: For embedding services
- **Gradio**: For the web interface


---

**Made with ❤️ for personalized learning**