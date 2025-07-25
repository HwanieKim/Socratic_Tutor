# Railway Deployment Guide 🚀

Complete guide for deploying the AI Socratic Tutor to Railway with PostgreSQL and file upload support.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gradio UI     │────│   TutorEngine    │────│  PostgreSQL DB  │
│ (File Upload)   │    │ (Session Mgmt)   │    │ (Metadata)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│Railway Volume   │    │   LlamaIndex     │    │   External APIs │
│(File Storage)   │    │ (Vector Index)   │    │ (Gemini/Voyage) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 New File Structure

```
example_rag/
├── railway_main.py              # Railway entry point
├── test_railway.py              # Integration tests
├── railway.toml                 # Railway configuration
├── requirements.txt             # Updated with PostgreSQL
├── src/
│   ├── core/
│   │   ├── database_manager.py  # NEW: PostgreSQL management
│   │   ├── tutor_engine.py      # Updated: Multi-user support
│   │   ├── persistence.py       # Updated: Dynamic file paths
│   │   ├── dialogue_generator.py # Updated: Filename only display
│   │   └── config.py            # Updated: Railway Volume paths
│   └── ui/
│       └── gradio_ui_railway.py # NEW: Upload + session management
└── .env.example                 # Updated: Railway environment vars
```

## 🚀 Railway Deployment Steps

### 1. Setup Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and create project
railway login
railway init
cd your-project

# Add PostgreSQL service
railway add postgresql

# Deploy from GitHub (recommended)
railway connect
```

### 2. Configure Environment Variables

In Railway Dashboard → Variables, add:

```bash
# Required API Keys
GOOGLE_API_KEY=your_google_gemini_key
VOYAGE_API_KEY=your_voyage_embedding_key
LLAMA_CLOUD_API_KEY=your_llamacloud_parsing_key

# Railway auto-provides these:
DATABASE_URL=postgresql://...  # Auto-generated
RAILWAY_VOLUME_MOUNT_PATH=/app/data  # Auto-generated
PORT=7860  # Auto-detected
```

### 3. Enable Railway Volumes

In `railway.toml`:

```toml
[experimental]
volumes = ["/app/data"]  # Persistent file storage
```

### 4. Deploy

```bash
# From local directory
railway up

# Or connect GitHub repository
railway connect
# Then push to main branch
```

## 💻 Local Development Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Local Database (Optional)

```bash
# Install PostgreSQL locally or use SQLite fallback
# The system will automatically fallback if no DATABASE_URL
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Test Locally

```bash
python test_railway.py
python railway_main.py
```

## 🎯 Key Features

### Multi-User Session Management

-   Each user gets unique session ID
-   Isolated document storage per session
-   Session-specific vector indexes
-   Database tracking of all sessions

### File Upload & Processing

-   Upload PDFs through Gradio interface
-   Files stored in Railway Volume (persistent)
-   Automatic deduplication via file hashing
-   Progress tracking and status updates

### Dynamic Index Creation

-   Index created from uploaded files
-   User-specific index directories
-   Database metadata tracking
-   Automatic engine reinitialization

### Database Integration

-   PostgreSQL for production
-   SQLite fallback for development
-   User session tracking
-   Document metadata storage
-   Conversation history (optional)

## 📊 Database Schema

```sql
-- Users and sessions
users (id, session_id, created_at, last_active)

-- Uploaded documents
documents (id, user_session_id, original_filename, display_name,
          file_hash, file_path, file_size, upload_date, status, indexed)

-- Index metadata
document_indexes (id, user_session_id, index_path, document_count,
                  created_at, is_active)

-- Conversation history (optional)
conversations (id, user_session_id, user_message, tutor_response,
               context_used, created_at)
```

## 🔄 User Flow

1. **Access App** → New session created automatically
2. **Upload PDFs** → Files saved to Railway Volume + DB metadata
3. **Create Index** → Vector index generated from uploaded files
4. **Start Tutoring** → Engine ready for intelligent conversations
5. **Session Persistence** → All data saved, can resume later

## 🛠️ API Endpoints & Components

### TutorEngine Methods

```python
# Session management
engine = TutorEngine(session_id="user_123")
engine.get_session_info()
engine.is_ready_for_tutoring()

# File management
engine.upload_documents(files)
engine.create_user_index()
engine.get_user_documents()

# Tutoring
response = engine.get_guidance(user_question)
engine.save_conversation(user_msg, tutor_response)
```

### Database Operations

```python
# User management
db.create_or_get_user(session_id)
db.get_user_documents(session_id)

# Index tracking
db.mark_documents_indexed(session_id, index_path)
db.get_active_index(session_id)

# Conversation history
db.save_conversation(session_id, user_msg, tutor_response)
```

## 🔧 Configuration Options

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=          # Gemini API for reasoning
VOYAGE_API_KEY=          # Voyage AI for embeddings
LLAMA_CLOUD_API_KEY=     # LlamaCloud for PDF parsing

# Railway Auto-Generated
DATABASE_URL=            # PostgreSQL connection
RAILWAY_VOLUME_MOUNT_PATH= # Persistent storage path
PORT=                    # HTTP port (default: 7860)

# Optional
DEBUG_MODE=true          # Enable debug logging
```

### File Paths

```python
# Railway Volume structure
/app/data/
├── user_uploads/
│   └── {session_id}/
│       └── {file_hash}_{filename}.pdf
└── user_indexes/
    └── {session_id}/
        ├── docstore.json
        ├── index_store.json
        └── vector_store.json
```

## 🚨 Important Notes

### Security

-   Session IDs are UUIDs (secure)
-   Files isolated per session
-   No cross-session data access
-   Database connection secured

### Performance

-   Vector indexes cached per session
-   Database connections pooled
-   File deduplication via hashing
-   Old session cleanup available

### Scalability

-   Horizontal scaling supported
-   Stateless application design
-   Database handles concurrency
-   Railway Volume shared across instances

## 🔍 Troubleshooting

### Common Issues

1. **No index found** → Upload PDFs and create index
2. **Engine not ready** → Wait for index creation to complete
3. **Database connection failed** → Check DATABASE_URL in Railway
4. **File upload failed** → Check Railway Volume configuration

### Debug Commands

```bash
# Test all components
python test_railway.py

# Check session status
engine.get_session_info()

# Manual index creation
python -c "from core.persistence import create_index_from_files; import asyncio; asyncio.run(create_index_from_files(['path/to/file.pdf'], 'output_dir'))"
```

## 🎉 Success Metrics

After successful deployment:

-   ✅ Multi-user file upload working
-   ✅ Dynamic index creation functioning
-   ✅ Database storing all metadata
-   ✅ Persistent file storage on Railway Volume
-   ✅ Session isolation maintained
-   ✅ Intelligent tutoring responses generated

---

Ready for Railway deployment! 🚀
