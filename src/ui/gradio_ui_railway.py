#!/usr/bin/env python3
"""
Railway-Ready Gradio UI with Manual Modal & Staged Upload

Features:
- Multi-user session management
- Staged file upload (DB save on user confirmation)
- Dynamic index creation
- Database integration
- Manual, dependency-free, multi-step tutorial modal
"""

import gradio as gr
import time
import sys
import os
import uuid

from pathlib import Path
from fastapi import FastAPI, Response

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tutor_engine import TutorEngine
from core.database_manager import DatabaseManager
from core.i18n import get_ui_text, UI_TEXTS

# --- Global variables and Session Management (Unchanged) ---
user_sessions = {}
current_session_id = None

def get_or_create_session(session_id: str = None) -> TutorEngine:
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

# --- [MODIFIED] Backend Functions for Staged File Upload ---

def handle_file_upload_staging(files,lang):
    """
    Handles file upload by staging them in a temporary state
    without saving them to the database immediately.
    """
    global current_session_id
    if not files:
        return get_ui_text("no_files_staged", lang), gr.update(visible=False), gr.update(visible=False), None, []

    engine = get_or_create_session(current_session_id)
    if not engine:
        return get_ui_text("session_error", lang), gr.update(visible=False), gr.update(visible=False), None, []

    try:
        current_hashes = [engine.db_manager.calculate_file_hash(file.name) for file in files]
    except FileNotFoundError:
        return get_ui_text("file_not_found_error", lang), gr.update(visible=False), gr.update(visible=False), None, files
    
    matched_index = engine.find_matching_index(current_hashes)

    file_names = [os.path.basename(file.name) for file in files]
    staged_msg = (
        f"{len(files)} file(s) staged for upload: \n" +
        "\n".join([f" - {name}" for name in file_names])
    )

    if matched_index:
        status_msg = f"{staged_msg}\n\n {get_ui_text('existing_index_found', lang)}"
        return(
            status_msg,
            gr.update(visible=True),
            gr.update(visible=False),
            matched_index['id'],
            files
        )
    else:
        status_msg = f"{staged_msg}\n\n {get_ui_text('no_index_found', lang)}"
        return (
            status_msg,
            gr.update(visible=False),
            gr.update(visible=True),
            None,
            files
        )
    
async def save_and_create_index(staged_files):
    """
    Saves the staged files to the database first,
    then creates an index from them. This is the user-confirmed action.
    """
    global current_session_id
    
    if not staged_files:
        yield "No files were staged. Please upload files first."
        return

    try:
        engine = get_or_create_session(current_session_id)
        if not engine:
            yield "No session available."
            return

        yield "Step 1/2: Saving files to permanent storage..."
        # This is where files are actually saved to the DB
        upload_result = engine.upload_files(staged_files)
        yield upload_result
        
        yield "\nStep 2/2: Creating index from saved files..."
        async for status_message in engine.create_user_index():
            yield status_message

    except Exception as e:
        yield f"Index creation failed: {str(e)}"


def format_session_info(session_info: dict) -> str:
    if 'error' in session_info: return f"Error: {session_info['error']}"
    return "".join([
        f"Session: {session_info['session_id'][:8]}...\n",
        f"Documents: {session_info['documents_count']} uploaded, {session_info['indexed_documents']} indexed\n",
        f"Engine: {'Ready' if session_info['engine_ready'] else 'Not Ready'}\n",
        f"Created: {session_info.get('user_created', 'Unknown')}\n"
    ])

def get_session_status():
    global current_session_id
    if current_session_id is None: return "No active session. Upload files to start."
    engine = user_sessions.get(current_session_id)
    if not engine: return "Session not found."
    return format_session_info(engine.get_session_info())

def get_tutor_response(user_input, conversation_history, lang):
    global current_session_id
    if not user_input.strip(): return conversation_history, ""

    conversation_history.append({"role": "user", "content": user_input})
    
    engine = get_or_create_session(current_session_id)
    if not engine or not engine.is_ready_for_tutoring():
        error_msg = get_ui_text("engine_not_ready", lang)
        conversation_history.append({"role": "assistant", "content": error_msg})
        return conversation_history, ""
    
    # Get tutor's response based on user input
    response = engine.get_guidance(user_input)
    engine.save_conversation(user_input, response)
    conversation_history.append({"role": "assistant", "content": response})
    return conversation_history, ""

def new_session():
    global current_session_id
    current_session_id = str(uuid.uuid4())
    return [], f"New session created: {current_session_id[:8]}...", "", ""

def reset_conversation():
    engine = get_or_create_session(current_session_id)
    if engine: engine.reset()
    return [], "Conversation reset successfully!"

async def handle_load_index_click(index_id):
    engine = get_or_create_session(current_session_id)
    if not index_id or not engine: return "Error."
    return await engine.load_existing_index(index_id)


# --- [FINAL VERSION] Gradio Interface Creation ---

def create_gradio_interface():
    """Create the main Gradio interface with a manual, dependency-free modal."""
    
    # This CSS is the core of the manual modal implementation.
    css = """
    #popup_modal_container {
        position: fixed !important; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0.75);
        display: flex; justify-content: center;
        align-items: center; z-index: 1000;
    }
    #popup_content_wrapper {
        background-color: #2b2f38; padding: 2.5rem; border-radius: 1rem;
        max-width: 600px; box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        border: 1px solid #444;
        position: relative;
    }
    #close_button {
        position: absolute !important;
        top: 1rem;
        right: 1.2rem;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important; /* Gradio 버튼 그림자 제거 */
        padding: 0 !important;      /* Gradio 버튼 패딩 제거 */
        margin: 0 !important;       /* Gradio 버튼 마진 제거 */
        min-width: 0 !important;    /* Gradio 버튼 최소 너비 제거 */
        width: auto !important;     /* Gradio 버튼 너비 자동 설정 */
        display: block !important;
        font-size: 1.8rem !important;
        font-weight: bold;
        color: #aaa !important;
        cursor: pointer;
        z-index: 1010;
        line-height: 1;
    }
    #close_button:hover {
        color: #fff !important;
    }
    """
    with gr.Blocks(title="PolyGlot Socratic Tutor", css=css, theme=gr.themes.Soft()) as interface:
        
        # --- State Management ---
        language_state = gr.State(value="en")
        step_state = gr.State(value=1)
        uploaded_files_state = gr.State([])
        matched_index_id = gr.State(value=None)

        # --- language selector ---
        with gr.Row():
            language_choices = [
                (data['language_name'], lang) for lang, data in UI_TEXTS.items()
            ]

            dynamic_label = "/".join([data['language_name'] for data in UI_TEXTS.values()])
            language_dropdown = gr.Dropdown(
                choices=language_choices,
                value="en",
                label=dynamic_label,
                interactive=True,
                scale=1

            )
            gr.Markdown("",scale=3)
        # --- Main Application Container (Initially Hidden) ---
        with gr.Column(visible=True) as main_app_container:
            app_title = gr.Markdown(get_ui_text('app_title', 'en'))
            app_header = gr.Markdown(get_ui_text('app_header', 'en'))
            with gr.Row():
                with gr.Column(scale=1):
                    session_header = gr.Markdown(get_ui_text('session_header','en'))
                    with gr.Row():
                        new_session_btn = gr.Button(get_ui_text('new_session_btn','en'), variant="secondary")
                        session_status_btn = gr.Button(get_ui_text('session_status_btn','en'), variant="secondary")
                    session_info_display = gr.Textbox(label= get_ui_text('session_status_label','en'), interactive=False, lines=4)

                    upload_header = gr.Markdown(get_ui_text('upload_header','en'))
                    file_upload = gr.Files(file_types=[".pdf"], file_count="multiple", label=get_ui_text('file_upload_label','en'))
                    upload_status = gr.Textbox(label=get_ui_text('upload_status_label','en'), interactive=False, lines=3)

                    setup_header =gr.Markdown(get_ui_text('setup_header','en'))
                    load_index_btn = gr.Button(get_ui_text('load_index_btn','en'), variant="secondary", visible=False)
                    create_index_btn = gr.Button(get_ui_text('create_index_btn','en'), variant="primary", visible=False)
                    setup_status = gr.Textbox(label=get_ui_text('setup_status_label','en'), interactive=False, lines=4)

                with gr.Column(scale=2):
                    conversation_header = gr.Markdown(get_ui_text('conversation_header','en'))
                    chat_disclaimer_md = gr.Markdown(f"*{get_ui_text('chat_disclaimer','en')}*")
                    chatbot = gr.Chatbot( height=600, show_label=False, type="messages")
                    with gr.Row():
                        user_input = gr.Textbox(label=get_ui_text('ask_question_label','en'), placeholder=get_ui_text('user_input_placeholder','en'), lines=2, scale=4)
                        send_btn = gr.Button(get_ui_text('send_btn','en'), variant="primary", scale=1)
                    with gr.Row():
                        reset_btn = gr.Button(get_ui_text('reset_btn','en'), variant="secondary")
                        clear_btn = gr.Button(get_ui_text('clear_btn','en'), variant="secondary")

        # --- Manual Modal/Popup Container (Initially Visible) ---
        with gr.Column(visible=True, elem_id="popup_modal_container") as popup_container:
            with gr.Column(elem_id="popup_content_wrapper"):
                close_btn = gr.Button("✖", elem_id="close_button")

                # Step 1: File Upload
                with gr.Column(visible=True) as step_1_container:
                    gr.Markdown("##  Step 1: Upload Your Documents")
                    gr.Markdown("### Drag & Drop or Click to Upload")
                    gr.Image(value="assets/upload.png", interactive=False, show_download_button=False, show_label=False)
                    gr.Markdown("Once uploaded, you will see a status update like this:")
                    gr.Markdown("### Upload Success")
                    gr.Image(value="assets/PDF_uploaded.png", interactive=False, show_download_button=False, show_label=False)
                    next_to_step_2_btn = gr.Button("Next Step", variant="primary")

                # Step 2: Index Creation
                with gr.Column(visible=False) as step_2_container:
                    gr.Markdown("## Step 2: Let the Socratic Tutor learn your documents")
                    gr.Markdown("After successful uploading, click the 'Create New Index' button that appears.")  
                    gr.Image(value="assets/setup_create_index.png", interactive=False, show_download_button=False, show_label=False)

                    gr.Markdown("The process may take a few minutes depending on the document size. You will see a completion status when it's done.")
                    gr.Image(value="assets/index_creating.png", interactive=False, show_download_button=False, show_label=False)
                    gr.Image(value="assets/index_success.png", interactive=False, show_download_button=False, show_label=False)
                    next_to_step_3_btn = gr.Button("Next Step", variant="primary")
                
                # Step 3: Start Tutoring
                with gr.Column(visible=False) as step_3_container:
                    gr.Markdown("## Step 3: Start Your Tutoring Session!")
                    gr.Markdown("Everything is ready! Start asking questions in the chat window.")
                    start_btn = gr.Button("Let's Get Started!", variant="primary")

        # --- Event Handlers & Connections ---
        
        # Language change handler
        def update_ui_language(lang):
             return {
                language_state: lang,
                app_title: gr.update(value=f"# {get_ui_text('app_title', lang)}"),
                app_header: gr.update(value=get_ui_text('app_header', lang)),
                session_header: gr.update(value=get_ui_text('session_header', lang)),
                new_session_btn: gr.update(value=get_ui_text('new_session_btn', lang)),
                session_status_btn: gr.update(value=get_ui_text('refresh_status_btn', lang)),
                session_info_display: gr.update(label=get_ui_text('session_status_label', lang)),
                upload_header: gr.update(value=get_ui_text('upload_header', lang)),
                file_upload: gr.update(label=get_ui_text('file_upload_label', lang)),
                upload_status: gr.update(label=get_ui_text('upload_status_label', lang)),
                setup_header: gr.update(value=get_ui_text('setup_header', lang)),
                load_index_btn: gr.update(value=get_ui_text('load_index_btn', lang)),
                create_index_btn: gr.update(value=get_ui_text('create_index_btn', lang)),
                setup_status: gr.update(label=get_ui_text('setup_status_label', lang)),
                conversation_header: gr.update(value=get_ui_text('conversation_header', lang)),
                chat_disclaimer_md: gr.update(value=f"*{get_ui_text('chat_disclaimer', lang)}*"),
                user_input: gr.update(label=get_ui_text('ask_question_label', lang)),
                send_btn: gr.update(value=get_ui_text('send_btn', lang)),
                reset_btn: gr.update(value=get_ui_text('reset_btn', lang)),
                clear_btn: gr.update(value=get_ui_text('clear_btn', lang)),
            }

        all_ui_outputs = [
            language_state, app_title, app_header, session_header, new_session_btn,
            session_status_btn, session_info_display, upload_header, file_upload,
            upload_status, setup_header, load_index_btn, create_index_btn,
            setup_status, conversation_header, chat_disclaimer_md, user_input,
            send_btn, reset_btn, clear_btn
        ]

        language_dropdown.change(
            fn=update_ui_language,
            inputs=[language_dropdown],
            outputs=all_ui_outputs
        )

        # Modal/Popup control functions
        def handle_next_step(current_step):
            new_step = current_step + 1
            return {
                step_state: new_step,
                step_1_container: gr.update(visible=(new_step == 1)),
                step_2_container: gr.update(visible=(new_step == 2)),
                step_3_container: gr.update(visible=(new_step == 3)),
            }

        def close_popup_and_reset():
            return {
                popup_container: gr.update(visible=False),
                main_app_container: gr.update(visible=True),
                step_state: 1,
                step_1_container: gr.update(visible=True),
                step_2_container: gr.update(visible=False),
                step_3_container: gr.update(visible=False),
            }

        # Connect modal buttons
        next_to_step_2_btn.click(fn=handle_next_step, inputs=[step_state], outputs=[step_state, step_1_container, step_2_container, step_3_container])
        next_to_step_3_btn.click(fn=handle_next_step, inputs=[step_state], outputs=[step_state, step_1_container, step_2_container, step_3_container])

        outputs_for_close = [popup_container, main_app_container, step_state, step_1_container, step_2_container, step_3_container]
        start_btn.click(
            fn=close_popup_and_reset,
            inputs=None,
            outputs=outputs_for_close
        ) \
                .then(
                    fn=get_session_status,
                    outputs=[session_info_display]
                )
        
        close_btn.click(
            fn=close_popup_and_reset,
            inputs=None,
            outputs=outputs_for_close
        ) \
                .then(
                    fn=get_session_status,
                    outputs=[session_info_display]
                )

        # Main application event handlers
        new_session_btn.click(
            new_session,
            outputs=[chatbot, session_info_display, upload_status, setup_status]
        )

        session_status_btn.click(
            get_session_status, outputs=[session_info_display]
        )

        # File upload and index creation
        file_upload.change(
            handle_file_upload_staging,
            inputs=[file_upload, language_state],
            outputs=[upload_status, load_index_btn, create_index_btn, matched_index_id, uploaded_files_state]
        )

        create_index_btn.click(
            save_and_create_index,
            inputs=[uploaded_files_state],
            outputs=[setup_status]
        )


        load_index_btn.click(
            handle_load_index_click,
            inputs=[matched_index_id],
            outputs=[setup_status]
        )

        send_btn.click(
            get_tutor_response,
            inputs=[user_input, chatbot, language_state],
            outputs=[chatbot, user_input]
        )

        user_input.submit(
            get_tutor_response,
            inputs=[user_input, chatbot, language_state],
            outputs=[chatbot, user_input]
        )

        reset_btn.click(
            reset_conversation,
            outputs=[chatbot, setup_status]
        )

        clear_btn.click(
            lambda: ([], ""), 
            outputs=[chatbot, user_input]
        )

        # Load initial session status when the app loads. The popup will appear on top.
        interface.load(fn=get_session_status, inputs=None, outputs=[session_info_display])

    return interface

# --- Main function to launch the app (Unchanged) ---
def main():
    print("Starting AI Tutor - Railway Edition")
    os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
    try:
        db = DatabaseManager()
        print("Database initialized")
    except Exception as e:
        print(f"Database initialization warning: {e}")
    
    interface = create_gradio_interface()
    app = FastAPI()

    @app.get("/health")
    def health_check():
        return Response(status_code=200, content="OK")

    app = gr.mount_gradio_app(app, interface, path="/app")
    port = int(os.getenv("PORT", 7860))
    
    print(f"Launching on 0.0.0.0:{port}")
    print("ጤ Health check endpoint available at /health")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()