#!/usr/bin/env python3
"""
Railway-Ready Gradio UI with File Upload Support

Features:
- Multi-user session management
- File upload to Railway Volume
- Dynamic index creation
- Database integration
- User document management
"""

import gradio as gr
import time
import sys
import os
import uuid
import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI, Response

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tutor_engine import TutorEngine
from core.database_manager import DatabaseManager

# Global variables for session management
user_sessions = {}  # session_id -> TutorEngine
current_session_id = None

def get_or_create_session(session_id: str = None) -> TutorEngine:
    """Get existing session or create new one"""
    global user_sessions, current_session_id
    
    if session_id is None:
        session_id = str(uuid.uuid4())
        current_session_id = session_id
    
    if session_id not in user_sessions:
        try:
            user_sessions[session_id] = TutorEngine(session_id=session_id)
            print(f"Created new session: {session_id}")
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    return user_sessions[session_id]

def handle_file_upload(files):
    """
    Handle file upload, and save to Railway Volume,
    updates dynamically ui button's state
    """
    global current_session_id

    engine = get_or_create_session(current_session_id)
    if not engine:
        return "Failed to create session.", "", gr.update(visible=False), gr.update(visible=False), None
    
    # upload file on server saving metadata to database
    upload_result = engine.upload_files(files)

    # matching with existing index
    matched_index = engine.find_matching_index(files)

    session_info = engine.get_session_info()
    session_display= format_session_info(session_info)

    # Update UI elements based on upload result
    if matched_index:
        print(f"Matched existing index: {matched_index}")
        return(
            upload_result,
            session_display,
            gr.update(visible=True, value=f"Load Index ({matched_index['document_count']} files)"),
            gr.update(visible=True),
            matched_index['id']
        )
    else:
        print("No matching index found.")
        return (
            upload_result,
            session_display,
            gr.update(visible=False),
            gr.update(visible=True, value="Create New Index"),
            None
        )

async def handle_load_index_click(index_id):
    """Handle click on load index button"""
    global current_session_id
    if not index_id:
        return "Error: No index selected."
    
    print(f"Loading index {index_id} for session {current_session_id}")

    engine = get_or_create_session(current_session_id)
    result = await engine.load_existing_index(index_id)
    return result



def create_index_from_uploaded_files():
    """Create index from uploaded files"""
    global current_session_id
    
    try:
        engine = get_or_create_session(current_session_id)
        if not engine:
            yield "No session available."
            return
        
        yield "🔄 Starting index creation..."
        
        # Create user index
        result = engine.create_user_index()
        
        yield result
        
        # Update session info
        session_info = engine.get_session_info()
        yield f"{result}\n\n📊 Session Status:\n{format_session_info(session_info)}"
        
    except Exception as e:
        yield f"Index creation failed: {str(e)}"

def format_session_info(session_info: dict) -> str:
    """Format session information for display"""
    if 'error' in session_info:
        return f"Error: {session_info['error']}"
    
    status_lines = [
        f"Session: {session_info['session_id'][:8]}...\n",
        f"Documents: {session_info['documents_count']} uploaded, {session_info['indexed_documents']} indexed\n",
        f"Engine: {'Ready' if session_info['engine_ready'] else 'Not Ready'}\n",
        f"Created: {session_info.get('user_created', 'Unknown')}\n"
    ]

    return "".join(status_lines)

def get_session_status():
    """Get current session status"""
    global current_session_id
    
    try:
        if current_session_id is None:
            return "No active session. Upload files to start."
        
        engine = user_sessions.get(current_session_id)
        if not engine:
            return "Session not found."
        
        session_info = engine.get_session_info()
        return format_session_info(session_info)
        
    except Exception as e:
        return f"Error getting status: {e}"

def get_tutor_response(user_input, conversation_history):
    """Get response from tutor engine"""
    global current_session_id
    
    if not user_input.strip():
        return conversation_history, ""
    
    try:
        engine = get_or_create_session(current_session_id)
        if not engine:
            error_msg = "No session available. Please upload documents first."
            conversation_history.append([user_input, error_msg])
            return conversation_history, ""
        
        if not engine.is_ready_for_tutoring():
            error_msg = "Engine not ready. Please upload documents and create index first."
            conversation_history.append([user_input, error_msg])
            return conversation_history, ""
        
        # Get tutor response
        start_time = time.time()
        response = engine.get_guidance(user_input)
        response_time = time.time() - start_time
        
        # Save conversation to database
        engine.save_conversation(user_input, response)
        
        # Add to conversation history
        conversation_history.append([user_input, response])
        
        # Add timing info if in debug mode
        if os.getenv("DEBUG_MODE"):
            response += f"\\n\\n_Response time: {response_time:.2f}s_"
        
        return conversation_history, ""
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        conversation_history.append([user_input, error_msg])
        return conversation_history, ""

def reset_conversation():
    """Reset conversation history"""
    global current_session_id
    
    try:
        engine = get_or_create_session(current_session_id)
        if engine and hasattr(engine, 'reset'):
            engine.reset()
        return [], "Conversation reset successfully!"
    except Exception as e:
        return [], f"Reset failed: {e}"

def new_session():
    """Start a new session"""
    global current_session_id, user_sessions
    
    # Create new session ID
    new_session_id = str(uuid.uuid4())
    current_session_id = new_session_id
    
    # Clean up old session if needed (keep last 5 sessions)
    if len(user_sessions) > 5:
        oldest_session = min(user_sessions.keys())
        del user_sessions[oldest_session]
    
    return [], f"New session created: {new_session_id[:8]}...", "", ""

def create_gradio_interface():
    """Create the main Gradio interface"""
    
    # Custom CSS for better styling
    css = """
    .session-info { background-color: #f0f8ff; padding: 10px; border-radius: 5px; margin: 10px 0; }
    .status-ready { color: #28a745; font-weight: bold; }
    .status-error { color: #dc3545; font-weight: bold; }
    .upload-area { border: 2px dashed #007bff; padding: 20px; border-radius: 10px; text-align: center; }
    """
    
    with gr.Blocks(title="PolyGlot Socratic Tutor", css=css, theme=gr.themes.Soft()) as interface:
        
        # Header
        gr.Markdown("""
        # Socratic Tutor 
        Upload your PDF documents and engage in intelligent tutoring sessions.""")
        
        with gr.Row():
            with gr.Column(scale=1):
                # Session Management
                gr.Markdown("##  Session Management")
                
                with gr.Row():
                    new_session_btn = gr.Button("New Session", variant="secondary")
                    session_status_btn = gr.Button(" Refresh Status", variant="secondary")
                
                session_info_display = gr.Textbox(
                    label="Session Status",
                    interactive=False,
                    lines=4,
                    elem_classes=["session-info"]
                )
                
                # File Upload Section
                gr.Markdown("## Upload Documents")
                
                file_upload = gr.Files(
                    file_types=[".pdf"],
                    file_count="multiple",
                    label="Upload PDF Documents",
                    elem_classes=["upload-area"]
                )
                
                upload_status = gr.Textbox(
                    label="Upload Status",
                    interactive=False,
                    lines=3
                )
                
                # Index Creation
                gr.Markdown("##  Setup")

                load_index_btn = gr.Button(
                    "Load Detected Index", 
                    variant="secondary", 
                    visible=False
                )

                create_index_btn = gr.Button(
                    " Create Index & Initialize Engine", 
                    variant="primary",
                    visible=False
                )

                matched_index_id = gr.State(value=None)

                setup_status = gr.Textbox(
                    label="Setup Status",
                    interactive=False,
                    lines=4
                )
                
            with gr.Column(scale=2):
                # Chat Interface
                gr.Markdown("## Tutoring Session")
                
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                    show_label=True,
                    type= "messages"  # Use messages type for better chat experience
                )
                
                with gr.Row():
                    user_input = gr.Textbox(
                        label="Ask a question",
                        placeholder="Type your question here...",
                        lines=2,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    reset_btn = gr.Button("Reset Conversation", variant="secondary")
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
        
        # Event Handlers
        
        # New session
        new_session_btn.click(
            new_session,
            outputs=[chatbot, session_info_display, upload_status, setup_status]
        )
        
        # Session status
        session_status_btn.click(
            get_session_status,
            outputs=[session_info_display]
        )
        
        # File upload
        file_upload.change(
            handle_file_upload,
            inputs=[file_upload],
            outputs=[upload_status, session_info_display,load_index_btn, create_index_btn, matched_index_id]
        )
        
        # Index creation
        create_index_btn.click(
            create_index_from_uploaded_files,
            outputs=[setup_status]
        )
        
        # Load existing index
        load_index_btn.click(
            handle_load_index_click,
            inputs=[matched_index_id],
            outputs=[setup_status]
        )
        # Chat functionality
        send_btn.click(
            get_tutor_response,
            inputs=[user_input, chatbot],
            outputs=[chatbot, user_input]
        )
        
        user_input.submit(
            get_tutor_response,
            inputs=[user_input, chatbot],
            outputs=[chatbot, user_input]
        )
        
        # Reset and clear
        reset_btn.click(
            reset_conversation,
            outputs=[chatbot, setup_status]
        )
        
        clear_btn.click(
            lambda: ([], ""),
            outputs=[chatbot, user_input]
        )
        
        # Initial status load
        interface.load(
            get_session_status,
            outputs=[session_info_display]
        )
    
    return interface

def main():
    """Main function to launch the interface"""
    print("Starting AI Tutor - Railway Edition")
    
    # Force production environment detection
    os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
    
    # Initialize database on startup
    try:
        db = DatabaseManager()
        print("Database initialized")
    except Exception as e:
        print(f"Database initialization warning: {e}")
    
    # Create and launch interface
    interface = create_gradio_interface()
    
    # Create a simple FastAPI app for the health check
    app = FastAPI()

    @app.get("/health")
    def health_check():
        return Response(status_code=200, content="OK")

    # Mount the Gradio app
    app = gr.mount_gradio_app(app, interface, path="/app")
    
    # Launch settings - Railway 최적화
    port = int(os.getenv("PORT", 7860))
    
    print(f"Launching on 0.0.0.0:{port}")
    print("ጤ Health check endpoint available at /health")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()