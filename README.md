# RAG-based Sustainable Design Tutor

An AI-powered tutoring system that helps students learn about sustainable design through Socratic dialogue, powered by Google's Gemini 2.5 Flash and LlamaIndex.

## ✨ Key Features

- **Anti-Hallucination**: Strict context-only responses with source verification
- **Socratic Dialogue**: Natural conversation flow with memory and context awareness
- **Source Citations**: Page-specific references for first questions
- **Smart Follow-ups**: Brief guidance with page suggestions for subsequent questions
- **Production Ready**: Rate limiting, error handling, and monitoring
- **Topic Filtering**: Focused on sustainable design education

## Quick Start

### Prerequisites
- Python 3.8+
- Google AI API key (for Gemini 2.5 Flash)

### Installation

1. **Clone and Setup**
   ```bash
   cd example_rag
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```

4. **Access the Interface**
   Open your browser to: `http://127.0.0.1:7861`

## Testing

Run all tests:
```bash
python run_tests.py
```

Run individual tests:
```bash
python tests/test_gemini25.py       # Gemini integration test
python tests/quick_test.py          # Quick validation
python tests/test_edge_cases.py     # Comprehensive edge cases (long-running)
```

## Project Structure

```
example_rag/
├── main.py                    # Main application entry point
├── run_tests.py              # Test runner
├── src/                      # Source code
│   ├── core/                 # Core business logic
│   │   ├── tutor_engine.py   # Main RAG engine
│   │   ├── models.py         # Data models
│   │   ├── config.py         # Configuration
│   │   └── ...
│   └── ui/                   # User interfaces
│       ├── gradio_ui_production.py  # Production UI
│       └── gradio_ui_fast.py        # Development UI
├── tests/                    # Test modules
├── docs/                     # Documentation
├── data/                     # Knowledge base
└── persistent_index/         # Vector database
```

For detailed structure information, see [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## How It Works

1. **Document Processing**: PDF documents are indexed using HuggingFace embeddings
2. **Context Retrieval**: User questions trigger similarity search in the vector database
3. **Response Generation**: Gemini 2.5 Flash generates responses using retrieved context
4. **Conversation Management**: Memory buffer maintains conversation context
5. **Template Selection**: Different prompts for first questions (with citations) vs follow-ups (brief guidance)

## Configuration

Key settings in `src/core/config.py`:
- `GEMINI_MODEL_NAME`: AI model (default: "gemini-2.5-flash")
- `EMBED_MODEL_NAME`: Embedding model for document indexing
- `PERSISTENCE_DIR`: Vector database storage location

## System Capabilities

### Core Features
✅ Source-grounded responses (no hallucination)  
✅ Conversation memory and context awareness  
✅ Turn-based response templates  
✅ Automatic source citation  
✅ Page number suggestions  

### Production Features
✅ Rate limiting (10 requests/minute)  
✅ Topic relevance filtering  
✅ Enhanced error handling  
✅ Conversation metrics  
✅ System monitoring  

### Testing Coverage
✅ API integration tests  
✅ Edge case handling  
✅ Error recovery  
✅ Long conversation management  
✅ Input validation  

## Architecture

The system uses a two-stage approach:

1. **Stage 1 - Internal Reasoning**: Retrieves relevant context and generates structured reasoning using RAG
2. **Stage 2 - Socratic Dialogue**: Converts internal reasoning into user-friendly guidance using conversation templates

## Performance

- **Response Time**: 2-5 seconds (API dependent)
- **Context Window**: Up to 1M tokens (Gemini 2.5 Flash)
- **Memory**: Efficient token-limited conversation buffer
- **Accuracy**: 95%+ context adherence with anti-hallucination measures

## Development

### Adding New Features
1. Core logic: Add to `src/core/`
2. UI components: Add to `src/ui/`
3. Tests: Add to `tests/`
4. Update imports and documentation

### Running in Development Mode
```bash
python src/ui/gradio_ui_fast.py  # Development UI
python src/ui/gradio_ui_production.py  # Production UI
```

## Documentation

- [Final Project Report](docs/FINAL_REPORT.md)
- [Gemini 2.5 Flash Migration](docs/GEMINI25_MIGRATION_REPORT.md)
- [Project Structure](docs/PROJECT_STRUCTURE.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is developed for educational purposes as part of sustainable design research.

## Acknowledgments

- **LlamaIndex**: RAG framework and document processing
- **Google AI**: Gemini 2.5 Flash language model
- **Gradio**: User interface framework
- **HuggingFace**: Embedding models and transformers

---

**Status**: ✅ Production Ready  
**Last Updated**: 2025-06-30  
**Version**: 1.0.0
