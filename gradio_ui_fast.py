import gradio as gr
import time
import threading
from tutor_engine import TutorEngine

class TutorUI:
    def __init__(self):
        """
        initialization:
        create TutorEngine instance and initialize conversation history
        """
        self.tutor = None
        self.is_loading = True
        self.conversation_history = []
        
        # background thread to initialize TutorEngine
        self.init_thread = threading.Thread(target=self._init_tutor_engine)
        self.init_thread.daemon = True
        self.init_thread.start()
    
    def _init_tutor_engine(self):
        """Background thread to initialize TutorEngine"""
        try:
            print("Initializing TutorEngine in the background...")
            self.tutor = TutorEngine()
            self.is_loading = False
            print("TutorEngine initialization complete")
        except Exception as e:
            print(f"TutorEngine initialization failed: {e}")
            self.is_loading = False
    
    def chat_with_tutor(self, user_message, history):
        """
        @param user_message: message from the user
        @param history: conversation history
        @output: tuple of (empty string, updated history)"""
        if not user_message.strip():
            return "", history

        # Check if the tutor engine is still loading
        if self.is_loading:
            response = "🔄 Tutor is preparing. Please wait a moment..."
        elif self.tutor is None:
            response = "❌ Tutor initialization failed. Please refresh the page."
        else:
            try:
                # Generate response from the tutor engine
                response = self.tutor.get_guidance(user_message)
            except Exception as e:
                response = f"error during response generation: {str(e)}"

        # Add to conversation history
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": response})
        
        return "", history
    
    def clear_conversation(self):
        """Clear conversation history"""
        if self.tutor:
            self.tutor.reset()
        return []
    
    def get_status(self):
        """Return current status of the tutor engine"""
        if self.is_loading:
            return "🔄 Initializing..."
        elif self.tutor is None:
            return "❌ Initialization failed"
        else:
            return "✅ Ready"

    def create_interface(self):
        """Create Gradio interface"""

        with gr.Blocks(title="Learning Tutor Bot") as demo:
            gr.Markdown(
                """
                # 🎓 Learning Tutor Bot

                Ask questions about sustainable design!
                """
            )
            
            # status display
            status_text = gr.Textbox(
                label="status   ", 
                value=self.get_status(),
                interactive=False,
                max_lines=1
            )
            
            # chat interface
            chatbot = gr.Chatbot(
                label="Chat",
                height=400,
                type="messages",
                placeholder="Conversation with the tutor will be displayed here..."
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="type your question",
                    placeholder="Ask a question about sustainable design...",
                    lines=2,
                    scale=4
                )
                submit_btn = gr.Button("Submit", variant="primary", scale=1)
            
            with gr.Row():
                clear_btn = gr.Button("Clear Conversation", variant="secondary")
                refresh_btn = gr.Button("Refresh Status", variant="secondary")

            # Example questions
            gr.Markdown("### 💡 Example Questions")
            with gr.Row():
                example_btn1 = gr.Button("What is sustainable design?", size="sm")
                example_btn2 = gr.Button("What are the key principles?", size="sm")
                example_btn3 = gr.Button("What is the product lifecycle?", size="sm")
            
            # 이벤트 핸들러들
            submit_btn.click(
                fn=self.chat_with_tutor,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            
            msg.submit(
                fn=self.chat_with_tutor,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            
            clear_btn.click(
                fn=self.clear_conversation,
                outputs=[chatbot]
            )
            
            refresh_btn.click(
                fn=self.get_status,
                outputs=[status_text]
            )
            
            # Example button events
            example_btn1.click(
                lambda: "what is a sustainable design?",
                outputs=[msg]
            )
            
            example_btn2.click(
                lambda: "What are the key principles of sustainable design?",
                outputs=[msg]
            )
            
            example_btn3.click(
                lambda: "What is the product lifecycle?",
                outputs=[msg]
            )
            
            # Status refresh, executed automatically on first load
            demo.load(
                fn=self.get_status,
                outputs=[status_text]
            )
        
        return demo

def main():
    print("Starting Tutor UI...")
    
    # Create TutorUI instance
    tutor_ui = TutorUI()

    # Create Gradio interface
    demo = tutor_ui.create_interface()

    # Launch app
    print("Starting web interface (Tutor engine loading in background)...")
    demo.launch(
        server_name="localhost",  # Use 'localhost' for local testing
        # Use a different port to avoid conflicts
        server_port=4300,  
        share=False,
        show_error=True,
        quiet=False
    )

if __name__ == "__main__":
    main()
