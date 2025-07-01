# Project Structure Documentation

## RAG-based Sustainable Design Tutor - Organized File Structure

This document describes the organized file structure of the RAG-based Sustainable Design Tutor project.

## Directory Structure

```
example_rag/
├── main.py                     # Main entry point for the application
├── run_tests.py               # Test runner script
├── .env                       # Environment variables (API keys)
├── .gitignore                 # Git ignore rules
├── README.md                  # Project overview and setup instructions
│
├── 📂 src/                    # Source code
│   ├── __init__.py
│   ├── main .py              # Original main file (legacy)
│   │
│   ├── 📂 core/              # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration settings
│   │   ├── models.py         # Pydantic data models
│   │   ├── tutor_engine.py   # Main RAG engine with conversation management
│   │   ├── prompts_template.py # Prompt templates for different scenarios
│   │   ├── persistence.py    # Document indexing and storage
│   │   └── production_enhancements.py # Rate limiting, filtering, metrics
│   │
│   ├── 📂 ui/                # User interface modules
│   │   ├── __init__.py
│   │   ├── gradio_ui_production.py # Production UI with all features
│   │   └── gradio_ui_fast.py       # Fast/development UI
│   │
│   └── 📂 utils/             # Utility modules (future use)
│       └── __init__.py
│
├── 📂 tests/                 # Test modules
│   ├── __init__.py
│   ├── test_gemini25.py      # Gemini 2.5 Flash integration tests
│   ├── test_edge_cases.py    # Comprehensive edge case testing
│   └── quick_test.py         # Quick validation tests
│
├── 📂 scripts/               # Utility and analysis scripts
│   ├── analysis_report.py    # Offline analysis tools
│   ├── final_report_generator.py # System completion report
│   └── gemini25_migration_report.py # Gemini migration report
│
├── 📂 docs/                  # Documentation
│   ├── FINAL_REPORT.md       # Complete project report
│   ├── GEMINI25_MIGRATION_REPORT.md # Migration documentation
│   └── PROJECT_STRUCTURE.md  # This file
│
├── 📂 data/                  # Knowledge base
│   └── Unit 1.4.pdf         # Sustainable design document
│
├── 📂 persistent_index/      # Vector database storage
│   ├── docstore.json
│   ├── index_store.json
│   └── default__vector_store.json
│
└── 📂 venv/                  # Python virtual environment
    └── ...
```

## 🎯 Module Descriptions

### Core Modules (`src/core/`)

- **`tutor_engine.py`**: The heart of the system containing the `TutorEngine` class that manages RAG operations, conversation memory, and response generation
- **`models.py`**: Pydantic data models for structured responses and type validation
- **`config.py`**: Configuration settings including model names, directories, and parameters
- **`prompts_template.py`**: Prompt templates for different conversation scenarios (first question vs follow-ups)
- **`persistence.py`**: Document indexing, vector storage, and retrieval functionality
- **`production_enhancements.py`**: Production-ready features including rate limiting, topic filtering, and metrics

### User Interface (`src/ui/`)

- **`gradio_ui_production.py`**: Full-featured production UI with all enhancements, monitoring, and error handling
- **`gradio_ui_fast.py`**: Simplified UI for development and testing purposes

### Tests (`tests/`)

- **`test_gemini25.py`**: Tests for Gemini 2.5 Flash integration and API functionality
- **`test_edge_cases.py`**: Comprehensive edge case testing including error scenarios, long conversations, and boundary conditions
- **`quick_test.py`**: Fast validation tests for basic functionality

### Scripts (`scripts/`)

- **`analysis_report.py`**: Offline analysis tools for system evaluation
- **`final_report_generator.py`**: Generates comprehensive project completion reports
- **`gemini25_migration_report.py`**: Documents the migration to Gemini 2.5 Flash

### Documentation (`docs/`)

- **`FINAL_REPORT.md`**: Complete project documentation and results
- **`GEMINI25_MIGRATION_REPORT.md`**: Technical details of the Gemini 2.5 Flash migration
- **`PROJECT_STRUCTURE.md`**: This documentation file

## 🚀 How to Run

### Production Application
```bash
python main.py
```

### Run Tests
```bash
python run_tests.py
```

### Direct UI Access
```bash
python src/ui/gradio_ui_production.py
```

### Individual Tests
```bash
python tests/test_gemini25.py
python tests/quick_test.py
```

## 📦 Import Structure

The project uses relative imports within modules and absolute imports from the root. The `main.py` and test files add the appropriate paths to `sys.path` for proper module resolution.

Example imports:
```python
# From core modules
from src.core.tutor_engine import TutorEngine
from src.core import config

# Within core modules
from .models import ReasoningTriplet
from .prompts_template import TUTOR_PROMPT_TEMPLATE
```

## 🔧 Key Features

1. **Modular Design**: Clear separation of concerns with dedicated modules for core logic, UI, and testing
2. **Production Ready**: Enhanced error handling, rate limiting, and monitoring
3. **Comprehensive Testing**: Multiple test suites covering integration, edge cases, and quick validation
4. **Documentation**: Thorough documentation of the system architecture and migration process
5. **Easy Deployment**: Simple entry points for running the application and tests

## 🎉 Benefits of This Structure

- **Maintainability**: Clear organization makes it easy to locate and modify specific functionality
- **Scalability**: Modular structure allows for easy addition of new features
- **Testing**: Comprehensive test coverage with organized test modules
- **Deployment**: Simple and clear entry points for different use cases
- **Documentation**: Well-documented structure and processes

This organized structure provides a solid foundation for the RAG-based Sustainable Design Tutor system, making it easy to maintain, extend, and deploy.
