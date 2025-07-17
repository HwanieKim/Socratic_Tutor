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

def initialize_engine():
    """Initialize the tutor engine"""
    global engine, prod_engine
    try:
        # Add debug information
        from core.config import PERSISTENCE_DIR, PROJECT_ROOT
        debug_info = f"Looking for index at: {PERSISTENCE_DIR}"
        print(f"DEBUG: {debug_info}")
        
        # Check if index exists
        if not os.path.exists(PERSISTENCE_DIR):
            # Try to create index automatically
            data_dir = os.path.join(PROJECT_ROOT, "data")
            if os.path.exists(data_dir) and os.listdir(data_dir):
                return f"❌ Index not found at: {PERSISTENCE_DIR}\n\n" + \
                       f"🔧 To create the index, run this command from the project root:\n" + \
                       f"python -c \"from src.core.persistence import *\"\n\n" + \
                       f"Or create the index manually by processing documents in: {data_dir}"
            else:
                return f"❌ Index not found at: {PERSISTENCE_DIR}\n" + \
                       f"❌ Data directory not found or empty at: {data_dir}\n\n" + \
                       f"Please add PDF documents to the data/ directory first."
        
        # List files in index directory
        index_files = os.listdir(PERSISTENCE_DIR)
        print(f"DEBUG: Index files found: {index_files}")
        
        # Check if required index files exist
        required_files = ['index_store.json', 'docstore.json', 'vector_store.json']
        missing_files = [f for f in required_files if f not in index_files and not any(f.startswith(f.split('_')[0]) for f in index_files)]
        
        if missing_files:
            return f"❌ Index directory exists but missing required files.\n" + \
                   f"Found: {index_files}\n" + \
                   f"Please recreate the index."
        
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
        return history + [{"role": "assistant", "content": "Please wait while the engine initializes..."}], ""
    
    if not user_input.strip():
        return history, ""
    
    try:
        # Get response from production engine
        response = prod_engine.get_guidance(user_input, user_id)
        
        # Add to conversation history using messages format
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})  # Changed from "tutor" to "assistant"
        
        return history, ""
        
    except Exception as e:
        error_response = f"I apologize, but I encountered an error: {str(e)}. Please try again."
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": error_response})  # Changed from "tutor" to "assistant"
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

def create_index():
    """Create the vector index from documents"""
    try:
        from core.persistence import create_index as create_index_async
        import asyncio
        
        # Check if index already exists
        from core.config import PERSISTENCE_DIR
        if os.path.exists(PERSISTENCE_DIR):
            return f"⚠️ Index already exists at: {PERSISTENCE_DIR}\n\nIf you want to recreate it, please delete the existing index directory first."
        
        # Check for data directory
        from core.persistence import DATA_DOCUMENTS_DIR
        if not os.path.exists(DATA_DOCUMENTS_DIR):
            return f"❌ Data directory not found at: {DATA_DOCUMENTS_DIR}\nPlease create the data/documents directory and add PDF documents."
        
        # Check for PDF files
        import glob
        pdf_files = glob.glob(os.path.join(DATA_DOCUMENTS_DIR, "*.pdf"))
        if not pdf_files:
            return f"❌ No PDF files found in: {DATA_DOCUMENTS_DIR}\nPlease add PDF documents to process."
        
        # Check for required API keys
        from dotenv import load_dotenv
        load_dotenv()
        
        llama_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        voyage_api_key = os.getenv("VOYAGE_API_KEY")
        
        if not llama_api_key:
            return "❌ LLAMA_CLOUD_API_KEY not found in environment variables."
        if not voyage_api_key:
            return "❌ VOYAGE_API_KEY not found in environment variables."
        
        # Run the async create_index function
        try:
            asyncio.run(create_index_async())
            return f"""✅ Index created successfully!
- Processed {len(pdf_files)} PDF files
- Saved to: {PERSISTENCE_DIR}
- Images saved to: {DATA_DOCUMENTS_DIR.replace('documents', 'images')}

You can now initialize the engine."""
        except Exception as e:
            return f"❌ Failed to create index: {str(e)}"
        
    except ImportError as e:
        return f"❌ Missing required dependencies: {str(e)}\nPlease install: pip install llama-cloud-services"
    except Exception as e:
        return f"❌ Failed to create index: {str(e)}"

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
                    type="messages"  # Changed from "tuples" to "messages"
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
                    create_index_btn = gr.Button("Create Index", variant="secondary", scale=1)
            
            with gr.Column(scale=1):
                # System information and controls
                gr.Markdown("### System Status")
                
                init_status = gr.Textbox(
                    label="Initialization Status",
                    value="Initializing...",
                    interactive=False,
                    lines=4
                )
                
                # Index management buttons
                with gr.Row():
                    init_btn = gr.Button("Initialize Engine", variant="primary", scale=1)
                
                gr.Markdown("""
                ### Setup Instructions
                1. **Create Index**: If index is missing, click "Create Index" first
                2. **Initialize Engine**: Click to start the tutor system
                3. **Start Chatting**: Ask questions about sustainable design
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
            create_index,
            outputs=[init_status]
        )
        
        # Initialize engine on load
        interface.load(
            initialize_engine,
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
    
    # Create and launch interface
    interface = create_gradio_interface()
    
    # Launch with appropriate settings
    interface.launch(
        server_name="127.0.0.1",
        server_port=7862,  # Use different port to avoid conflict
        show_error=True,
        share=False,
        inbrowser=True
    )

if __name__ == "__main__":
    main()
