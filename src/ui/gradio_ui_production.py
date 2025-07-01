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
        engine = TutorEngine()
        prod_engine = ProductionTutorEngine(engine)
        return "✅ Engine initialized successfully!"
    except Exception as e:
        return f"❌ Failed to initialize engine: {str(e)}"

def get_response(user_input, history, user_id="default"):
    """Get response from the tutor engine"""
    if not prod_engine:
        return history + [("System", "Please wait while the engine initializes...")], ""
    
    if not user_input.strip():
        return history, ""
    
    try:
        # Get response from production engine
        response = prod_engine.get_guidance(user_input, user_id)
        
        # Add to conversation history
        history.append((user_input, response))
        
        return history, ""
        
    except Exception as e:
        error_response = f"I apologize, but I encountered an error: {str(e)}. Please try again."
        history.append((user_input, error_response))
        return history, ""

def reset_conversation():
    """Reset the conversation"""
    if prod_engine:
        prod_engine.reset()
    return [], "Conversation reset. How can I help you with sustainable design?"

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
    .metrics-box {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 8px;
        font-family: monospace;
    }
    """
    
    with gr.Blocks(css=css, title="RAG Tutor - Sustainable Design Assistant") as interface:
        gr.Markdown("""
        # Sustainable Design Tutor
        
        An AI-powered tutor that helps you learn about sustainable design through Socratic dialogue.
        
        **Features:**
        - Sources answers from sustainable design documents
        - Provides context-aware follow-up guidance
        - Cites specific pages for first questions
        - ⚡ Gives concise guidance for follow-ups
        - Enhanced error handling and rate limiting
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                # Chat interface
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=400,
                    avatar_images=("User", "Bot"),
                    type="tuples"  # Explicitly set to avoid deprecation warning
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
                    metrics_btn = gr.Button("Show Metrics", variant="secondary", scale=1)
            
            with gr.Column(scale=1):
                # System information and controls
                gr.Markdown("### System Status")
                
                init_status = gr.Textbox(
                    label="Initialization Status",
                    value="Initializing...",
                    interactive=False
                )
                
                metrics_display = gr.Markdown(
                    "Click 'Show Metrics' to see system statistics.",
                    elem_classes=["metrics-box"]
                )
                
                gr.Markdown("""
                ### Tips
                - Start with broad questions about sustainable design
                - Follow up with "Can you tell me more?" or "What about...?"
                - Ask for specific examples or applications
                - Use "Reset" to start a fresh conversation
                """)
                
                gr.Markdown("""
                ### Note
                This tutor is specialized in sustainable design topics. 
                Off-topic questions will be redirected to relevant content.
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
        
        metrics_btn.click(
            get_system_metrics,
            outputs=[metrics_display]
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
