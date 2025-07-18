#!/usr/bin/env python3
"""
Production-Ready Gradio UI with Enhanced Features

This version includes all the improvements from edge case testing:
- Better error handling
- Rate limiting
- Topic relevance filtering
- Conversation metrics
- Enhanced logging
"""

import gradio as gr
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tutor_engine import TutorEngine
from core.production_enhancements import ProductionTutorEngine

# Global engine instance
engine = None
prod_engine = None

def check_index_exists():
    """Check if index exists without initializing engine"""
    try:
        from core.config import PERSISTENCE_DIR
        return os.path.exists(PERSISTENCE_DIR) and len(os.listdir(PERSISTENCE_DIR)) > 0
    except:
        return False
    
def initialize_engine():
    """Initialize the tutor engine"""
    global engine, prod_engine

    if engine is not None and prod_engine is not None:
        return "✅ Engine already initialized and ready!"
    
    # Check if index exists first
    if not check_index_exists():
        return "⚠️ No index found. Please create an index first using the 'Create Index' button below."
    
    try:
        # Add debug information
        from core.config import PERSISTENCE_DIR
        
        # List files in index directory
        index_files = os.listdir(PERSISTENCE_DIR)
        print(f"DEBUG: Index files found: {index_files}")
        
        # Check if required index files exist
        required_files = ['index_store.json', 'docstore.json', 'vector_store.json']
        missing_files = [f for f in required_files if f not in index_files and not any(f.startswith(f.split('_')[0]) for f in index_files)]
        
        if missing_files:
            return f"❌ Index directory exists but missing required files.\n" + \
                   f"Found: {index_files}\n" + \
                   f"Please recreate the index using 'Create Index' button."
        
        engine = TutorEngine()
        prod_engine = ProductionTutorEngine(engine)
        success_msg = f"✅ Engine initialized successfully!\nIndex loaded from: {PERSISTENCE_DIR}\nFiles: {len(index_files)} files"
        print(f"SUCCESS: {success_msg}")
        return success_msg
    except Exception as e:
        from core import config
        error_msg = f"❌ Failed to initialize engine: {str(e)}\n\nDebug info:\n- Index path: {getattr(config, 'PERSISTENCE_DIR', 'Unknown')}\n- Error type: {type(e).__name__}"
        print(f"ERROR: {error_msg}")
        return error_msg

def get_response(user_input, history, user_id="default"):
    """Get response from the tutor engine"""
    if not prod_engine:
        error_msg = "🚫 Engine not initialized. Please initialize the engine first."
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": error_msg})
        return history, ""
    
    if not user_input.strip():
        return history, ""
    
    try:
        # Get response from production engine
        response = prod_engine.get_guidance(user_input, user_id)
        
        # Add to conversation history using messages format
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        
        return history, ""
        
    except Exception as e:
        error_response = f"I apologize, but I encountered an error: {str(e)}. Please try again."
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": error_response})
        return history, ""

def reset_conversation():
    """Reset the conversation"""
    if prod_engine:
        prod_engine.reset()
    return [], ""  # Return empty list for messages format

def get_system_metrics():
    """Get system metrics for monitoring"""
    if not prod_engine:
        return "Engine not initialized"
    
    try:
        metrics = prod_engine.get_metrics()
        return f"""
**System Metrics**
- Total Questions: {metrics.get('total_questions', 0)}
- Avg Question Length: {metrics.get('avg_question_length', 0)} characters
- Avg Response Length: {metrics.get('avg_response_length', 0)} characters
- Interactions (Last Hour): {metrics.get('interactions_last_hour', 0)}
        """.strip()
    except Exception as e:
        return f"Error getting metrics: {str(e)}"

def create_index_with_progress():
    """Create the vector index from documents with progress updates"""
    try:
        # Check if index already exists
        from core.config import PERSISTENCE_DIR
        if os.path.exists(PERSISTENCE_DIR) and os.listdir(PERSISTENCE_DIR):
            return f"⚠️ Index already exists at: {PERSISTENCE_DIR}\n\nTo recreate, please delete the existing index directory first."
        
        # Check for data directory
        try:
            from core.persistence import DATA_DOCUMENTS_DIR
        except ImportError:
            # Fallback to default path if import fails
            DATA_DOCUMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "documents")
        
        if not os.path.exists(DATA_DOCUMENTS_DIR):
            return f"❌ Data directory not found at: {DATA_DOCUMENTS_DIR}\n\nPlease create the data/documents directory and add PDF documents."
        
        # Check for PDF files
        import glob
        pdf_files = glob.glob(os.path.join(DATA_DOCUMENTS_DIR, "*.pdf"))
        if not pdf_files:
            return f"❌ No PDF files found in: {DATA_DOCUMENTS_DIR}\n\nPlease add PDF documents to process."
        
        # Check for required API keys
        from dotenv import load_dotenv
        load_dotenv()
        
        llama_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        voyage_api_key = os.getenv("VOYAGE_API_KEY")
        
        missing_keys = []
        if not llama_api_key:
            missing_keys.append("LLAMA_CLOUD_API_KEY")
        if not voyage_api_key:
            missing_keys.append("VOYAGE_API_KEY")
        
        if missing_keys:
            return f"❌ Missing environment variables: {', '.join(missing_keys)}\n\nPlease set these in your .env file."
        
        # Import and run index creation
        yield f"🔄 Starting index creation...\nFound {len(pdf_files)} PDF files to process."
        
        try:
            from core.persistence import create_index as create_index_async
            import asyncio
            
            yield "🔄 Processing documents and creating embeddings...\nThis may take several minutes."
            
            # Run the async create_index function
            asyncio.run(create_index_async())
            
            yield f"""✅ Index created successfully!
- Processed {len(pdf_files)} PDF files
- Saved to: {PERSISTENCE_DIR}
- Ready for engine initialization

You can now click 'Initialize Engine' to start the tutor."""
            
        except Exception as e:
            yield f"❌ Failed to create index: {str(e)}\n\nPlease check your API keys and try again."
        
    except ImportError as e:
        yield f"❌ Missing required dependencies: {str(e)}\n\nPlease install: pip install llama-cloud-services"
    except Exception as e:
        yield f"❌ Failed to create index: {str(e)}"

def get_initial_status():
    """Get initial status message"""
    if check_index_exists():
        return "📋 Index found! Click 'Initialize Engine' to start the tutor."
    else:
        return "📋 Ready to start! Click 'Create Index' first, then 'Initialize Engine'."

def create_gradio_interface():
    """Create the Gradio interface"""
    
    # Custom CSS for better styling
    css = """
    .chat-container {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        background-color: #fafafa;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 8px;
        border-radius: 8px;
        margin: 5px 0;
        text-align: right;
    }
    .bot-message {
        background-color: #f1f8e9;
        padding: 8px;
        border-radius: 8px;
        margin: 5px 0;
    }
    """
    
    with gr.Blocks(css=css, title="PolyGlot Socratic Tutor") as interface:
        gr.Markdown("""
        # PolyGlot Socratic Tutor
        
        An AI-powered tutor that helps you learn through Socratic dialogue.
        
        **Features:**
        - Sources answers from uploaded documents by teacher
        - Provides context-aware follow-up guidance
        - Gives concise guidance for follow-ups
                    
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                # Chat interface - Updated to use messages format
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=400,
                    avatar_images=None,
                    type="messages"
                )
                
                with gr.Row():
                    user_input = gr.Textbox(
                        placeholder="Ask me about sustainable design...",
                        label="Your Question",
                        lines=2,
                        scale=4
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    reset_btn = gr.Button("Reset Conversation", variant="secondary", scale=1)
            
            with gr.Column(scale=1):
                # System information and controls
                gr.Markdown("### System Status")
                
                init_status = gr.Textbox(
                    label="Status",
                    value=get_initial_status(),
                    interactive=False,
                    lines=4
                )
                
                # Setup buttons
                gr.Markdown("### Setup Steps")
                create_index_btn = gr.Button("1. Create Index", variant="secondary", scale=1)
                init_btn = gr.Button("2. Initialize Engine", variant="primary", scale=1)
                
                gr.Markdown("""
                ### Instructions
                1. **First Time Setup**: Click "Create Index" to process your PDF documents
                2. **Initialize**: Click "Initialize Engine" to start the tutor
                3. **Chat**: Ask questions about your documents
                
                **Note**: Index creation may take several minutes depending on document size.
                """)
        
        # Event handlers
        def submit_and_clear(user_input, history):
            new_history, _ = get_response(user_input, history)
            return new_history, ""
        
        # Button events
        submit_btn.click(
            submit_and_clear,
            inputs=[user_input, chatbot],
            outputs=[chatbot, user_input]
        )
        
        user_input.submit(
            submit_and_clear,
            inputs=[user_input, chatbot],
            outputs=[chatbot, user_input]
        )
        
        reset_btn.click(
            reset_conversation,
            outputs=[chatbot, user_input]
        )
        
        init_btn.click(
            initialize_engine,
            outputs=[init_status]
        )
        
        create_index_btn.click(
            create_index_with_progress,
            outputs=[init_status]
        )
    
    return interface

def main():
    """Main function to run the application"""
    print("Starting Production RAG Tutor...")
    print("Features enabled:")
    print("  ✅ Enhanced error handling")
    print("  ✅ Rate limiting")
    print("  ✅ Topic relevance filtering")
    print("  ✅ Conversation metrics")
    print("  ✅ Enhanced logging")
    print("  ✅ Lazy index creation")
    
    # Create and launch interface
    interface = create_gradio_interface()
    
    # Launch with appropriate settings
    interface.launch(
        server_name="0.0.0.0",
        server_port=7862,
        show_error=True,
        share=False,
        inbrowser=True
    )

if __name__ == "__main__":
    main()
