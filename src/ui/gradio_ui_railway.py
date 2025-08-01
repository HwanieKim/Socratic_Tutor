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
import asyncio

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Response
from requests import session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tutor_engine import TutorEngine
from core.database_manager import DatabaseManager
from core.i18n import get_ui_text, UI_TEXTS

# --- Global variables and Session Management (Unchanged) ---
user_sessions = {}
current_session_id = None

def get_or_create_session(session_id: str = None, lang: str = "en") -> TutorEngine:
    """
    Gets the TutorEngine for a given session_id.
    If no session_id is provided, it returns the default engine instance.
    If the session is not found, it creates a new one.
    """
    global user_sessions, current_session_id
    
    if session_id is None:
        # If no session_id is provided, use the current global session_id
        session_id = current_session_id
        if session_id is None:
            # If there's no global session_id, create a new one.
            # This handles the very first interaction.
            session_id = str(uuid.uuid4())
            current_session_id = session_id

    if session_id not in user_sessions:
        try:
            print(f"Session {session_id} not found, creating new instance.")
            user_sessions[session_id] = TutorEngine(session_id=session_id, language=lang)
        except Exception as e:
            print(f"Error creating session {session_id}: {e}")
            return None
            
    return user_sessions.get(session_id)

# --- [MODIFIED] Backend Functions for Staged File Upload ---

def handle_file_upload_staging(files, lang='en'):
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
    
    # Use translated strings
    staged_msg = get_ui_text('files_staged', lang).format(
        count=len(files),
        filenames='\n'.join([f" - {name}" for name in file_names])
    )

    if matched_index:
        status_msg = f"{staged_msg}\n\n{get_ui_text('existing_index_found', lang)}"
        return(
            status_msg,
            gr.update(visible=True),
            gr.update(visible=False),
            matched_index['id'],
            files
        )
    else:
        status_msg = f"{staged_msg}\n\n{get_ui_text('no_index_found', lang)}"
        return (
            status_msg,
            gr.update(visible=False),
            gr.update(visible=True),
            None,
            files
        )
    
async def save_and_create_index(staged_files, lang='en'):
    """
    Saves the staged files to the database first,
    then creates an index from them. This is the user-confirmed action.
    """
    global current_session_id
    
    if not staged_files:
        yield get_ui_text("no_files_staged_for_creation", lang)
        return

    try:
        engine = get_or_create_session(current_session_id)
        if not engine:
            yield get_ui_text("session_error", lang)
            return

        yield get_ui_text("index_creation_step1", lang)
        # This is where files are actually saved to the DB
        upload_result = engine.upload_files(staged_files)
        yield upload_result
        
        yield f"\n{get_ui_text('index_creation_step2', lang)}"
        async for status_message in engine.create_user_index():
            yield status_message

    except Exception as e:
        yield f"{get_ui_text('index_creation_failed', lang)}: {str(e)}"


def get_session_status(lang='en'):
    global current_session_id
    if current_session_id is None: 
        return get_ui_text('no_active_session', lang)
    
    try:
        engine = user_sessions.get(current_session_id)
        if not engine: 
            return get_ui_text('session_not_found', lang)
    
        session_info = engine.get_session_info()
        
        # Format the session info using translated keys
        if 'error' in session_info:
            return f"{get_ui_text('error_prefix', lang)}: {session_info['error']}"

        return "".join([
            f"{get_ui_text('session_id_prefix', lang)}: {session_info['session_id'][:8]}...\n",
            f"{get_ui_text('documents_prefix', lang)}: {session_info['documents_count']} {get_ui_text('documents_uploaded_suffix', lang)}, {session_info['indexed_documents']} {get_ui_text('documents_indexed_suffix', lang)}\n",
            f"{get_ui_text('engine_status_prefix', lang)}: {get_ui_text('engine_ready', lang) if session_info['engine_ready'] else get_ui_text('engine_not_ready', lang)}\n",
            f"{get_ui_text('created_at_prefix', lang)}: {session_info.get('user_created', get_ui_text('unknown', lang))}\n"
        ])
    except Exception as e:
        print(f"Error retrieving session status: {e}")
        return get_ui_text('session_status_error', lang)

async def get_tutor_response(user_input, conversation_history, lang):
    global current_session_id
    if not user_input.strip(): return conversation_history, ""

    conversation_history.append({"role": "user", "content": user_input})
    
    engine = get_or_create_session(current_session_id)
    if not engine:
        error_msg = get_ui_text("session_error", lang)
        conversation_history.append({"role": "assistant", "content": error_msg})
        return conversation_history, ""
    
    # Enhanced step validation with detailed messages
    if not engine.can_start_tutoring():
        status = engine.get_tutoring_status()
        
        if not status['step1_upload_complete']:
            error_msg = get_ui_text("upload_documents_first", lang)
            additional_info = "\n\n💡 " + get_ui_text("tutorial_step1_desc", lang)
            error_msg += additional_info
        elif not status['step2_index_complete']:
            error_msg = get_ui_text("create_index_first", lang)
            additional_info = "\n\n💡 " + get_ui_text("tutorial_step2_desc", lang)
            error_msg += additional_info
        else:
            error_msg = get_ui_text("system_not_ready", lang)
        
        conversation_history.append({"role": "assistant", "content": error_msg})
        return conversation_history, ""
    
    try:
        # Get tutor's response based on user input
        response = await engine.get_guidance(user_input)
        engine.save_conversation(user_input, response)
        conversation_history.append({"role": "assistant", "content": response})
        return conversation_history, ""
    except Exception as e:
        error_msg = f"{get_ui_text('chat_error', lang)}: {str(e)}"
        conversation_history.append({"role": "assistant", "content": error_msg})
        return conversation_history, ""

def new_session(lang='en'):
    """
    Creates a new user session by generating a new UUID,
    and creating a new TutorEngine instance for it.
    """
    global current_session_id, user_sessions
    
    new_session_id = str(uuid.uuid4())
    current_session_id = new_session_id
    
    # Eagerly create the new TutorEngine instance
    user_sessions[new_session_id] = TutorEngine(session_id=new_session_id)
    print(f"Eagerly created new session and engine for: {new_session_id}")

    session_created_msg = get_ui_text('session_created', lang).format(session_id=new_session_id[:8])
    return [], session_created_msg, "", ""

def reset_conversation(lang='en'):
    engine = get_or_create_session(current_session_id)
    if engine: engine.reset()
    return [], get_ui_text('conversation_reset', lang)

def update_chat_availability(lang='en'):
    """Update chat input availability based on tutoring readiness"""
    global current_session_id
    
    if not current_session_id:
        return gr.update(
            interactive=False, 
            placeholder=get_ui_text("chat_disabled_step1", lang)
        )
    
    engine = get_or_create_session(current_session_id)
    if not engine:
        return gr.update(
            interactive=False, 
            placeholder=get_ui_text("session_error", lang)
        )
    
    status = engine.get_tutoring_status()
    
    if not status['step1_upload_complete']:
        return gr.update(
            interactive=False, 
            placeholder=get_ui_text("chat_disabled_step1", lang)
        )
    elif not status['step2_index_complete']:
        return gr.update(
            interactive=False, 
            placeholder=get_ui_text("chat_disabled_step2", lang)
        )
    else:
        return gr.update(
            interactive=True, 
            placeholder=get_ui_text("chat_enabled_ready", lang)
        )

def check_and_update_ui_state(lang='en'):
    """Check current state and return UI updates"""
    global current_session_id
    
    engine = get_or_create_session(current_session_id)
    status = engine.get_tutoring_status() if engine else {}
    
    # Chat input update
    chat_update = update_chat_availability(lang)
    
    # Status message and progress with enhanced messaging
    if not status.get('step1_upload_complete', False):
        status_msg = get_ui_text("tutorial_step1_title", lang) + ": " + get_ui_text("tutorial_step1_desc", lang)
        progress = get_ui_text("progress_waiting_upload", lang)
    elif not status.get('step2_index_complete', False):
        count = status.get('documents_count', 0)
        status_msg = get_ui_text("tutorial_step2_title", lang) + f": {count} " + get_ui_text("documents_uploaded_suffix", lang)
        progress = get_ui_text("progress_waiting_index", lang)
    else:
        count = status.get('indexed_count', 0)
        status_msg = get_ui_text("tutorial_step3_title", lang) + f": {count} " + get_ui_text("documents_indexed_suffix", lang)
        progress = get_ui_text("progress_all_complete", lang)
    
    return chat_update, status_msg, progress

def get_tutorial_message(step: int, lang='en') -> str:
    """Get tutorial message for current step"""
    if step == 1:
        return f"🚀 {get_ui_text('tutorial_step1_title', lang)}\n\n{get_ui_text('tutorial_step1_desc', lang)}"
    elif step == 2:
        return f"⚙️ {get_ui_text('tutorial_step2_title', lang)}\n\n{get_ui_text('tutorial_step2_desc', lang)}"
    else:
        return f"✅ {get_ui_text('tutorial_step3_title', lang)}\n\n{get_ui_text('tutorial_step3_desc', lang)}"

def get_step_from_status(status: dict) -> int:
    """Determine current step from engine status"""
    if not status.get('step1_upload_complete', False):
        return 1
    elif not status.get('step2_index_complete', False):
        return 2
    else:
        return 3

def is_chat_blocked(lang='en') -> tuple:
    """Check if chat should be blocked and return status info"""
    global current_session_id
    
    if not current_session_id:
        return True, get_ui_text("chat_disabled_step1", lang), 1
    
    engine = get_or_create_session(current_session_id)
    if not engine:
        return True, get_ui_text("session_error", lang), 1
    
    status = engine.get_tutoring_status()
    step = get_step_from_status(status)
    
    if step == 1:
        return True, get_ui_text("chat_disabled_step1", lang), step
    elif step == 2:
        return True, get_ui_text("chat_disabled_step2", lang), step
    else:
        return False, get_ui_text("chat_enabled_ready", lang), step

async def handle_load_index_click(index_id, lang='en'):
    engine = get_or_create_session(current_session_id)
    if not index_id or not engine: return get_ui_text('index_load_error', lang)
    
    # Use an async generator to yield status updates
    status_updates = []
    async for message in engine.load_existing_index(index_id):
        status_updates.append(message)
        # We return the final message, but you could also yield here if Gradio supported it directly
    return "\n".join(status_updates)


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

        # --- Main Application Container (Initially Hidden) ---
        with gr.Column(visible=True) as main_app_container:
        # --- language selector ---
           
            app_title = gr.Markdown(f"# {get_ui_text('app_title', 'en')}", elem_id="app_title")
            app_header = gr.Markdown(get_ui_text('app_header', 'en'), elem_id="app_header")
            
                    
            with gr.Row():
                with gr.Column(scale=1):
                    session_header = gr.Markdown(f"### {get_ui_text('session_header','en')}")
                    with gr.Row():
                        new_session_btn = gr.Button(get_ui_text('new_session_btn','en'), variant="secondary")
                        session_status_btn = gr.Button(get_ui_text('refresh_status_btn','en'), variant="secondary")
                        
                        language_choices = [
                        (data['language_name'], lang) for lang, data in UI_TEXTS.items()
                        ]

                        language_dropdown = gr.Dropdown(
                        choices=language_choices,
                        value="en",
                        label=get_ui_text('language_label', 'en'),
                        interactive=True,
                        container=False,
                        scale=1
                        )
                        
                    session_info_display = gr.Textbox(label= get_ui_text('session_status_label','en'), interactive=False, lines=4)
                    
                    # Enhanced status displays for step progress with better messaging
                    status_display = gr.Markdown(get_ui_text("tutorial_step1_title", "en") + ": " + get_ui_text("tutorial_step1_desc", "en"))
                    progress_display = gr.Markdown(get_ui_text("progress_waiting_upload", "en"))

                    upload_header = gr.Markdown(f"### {get_ui_text('upload_header','en')}")
                    file_upload = gr.Files(file_types=[".pdf"], file_count="multiple", label=get_ui_text('file_upload_label','en'))
                    upload_status = gr.Textbox(label=get_ui_text('upload_status_label','en'), interactive=False, lines=3)

                    setup_header =gr.Markdown(f"### {get_ui_text('setup_header','en')}")
                    load_index_btn = gr.Button(get_ui_text('load_index_btn','en'), variant="secondary", visible=False)
                    create_index_btn = gr.Button(get_ui_text('create_index_btn','en'), variant="primary", visible=False)
                    setup_status = gr.Textbox(label=get_ui_text('setup_status_label','en'), interactive=False, lines=4)

                with gr.Column(scale=2):
                    conversation_header = gr.Markdown(f"### {get_ui_text('conversation_header','en')}")
                    chat_disclaimer_md = gr.Markdown(f"*{get_ui_text('chat_disclaimer','en')}*")
                    chatbot = gr.Chatbot( height=600, show_label=False, type="messages")
                    with gr.Row():
                        user_input = gr.Textbox(
                            label=get_ui_text('ask_question_label','en'), 
                            placeholder=get_ui_text('chat_disabled_step1','en'), 
                            lines=2, 
                            scale=4,
                            interactive=False  # Start disabled
                        )
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
                    modal_step1_header = gr.Markdown(f"## {get_ui_text('modal_step1_header', 'en')}")
                    modal_step1_subheader = gr.Markdown(f"### {get_ui_text('modal_step1_subheader', 'en')}")
                    gr.Image(value="assets/upload.png", interactive=False, show_download_button=False, show_label=False)
                    modal_step1_info = gr.Markdown(get_ui_text('modal_step1_info', 'en'))
                    modal_step1_success_header = gr.Markdown(f"### {get_ui_text('modal_step1_success_header', 'en')}")
                    gr.Image(value="assets/PDF_uploaded.png", interactive=False, show_download_button=False, show_label=False)
                    next_to_step_2_btn = gr.Button(get_ui_text('modal_next_btn', 'en'), variant="primary")

                # Step 2: Index Creation
                with gr.Column(visible=False) as step_2_container:
                    modal_step2_header = gr.Markdown(f"## {get_ui_text('modal_step2_header', 'en')}")
                    modal_step2_subheader = gr.Markdown(get_ui_text('modal_step2_subheader', 'en'))
                    gr.Image(value="assets/setup_create_index.png", interactive=False, show_download_button=False, show_label=False)

                    modal_step2_detail = gr.Markdown(get_ui_text('modal_step2_detail', 'en'))
                    gr.Image(value="assets/index_creating.png", interactive=False, show_download_button=False, show_label=False)
                    gr.Image(value="assets/index_success.png", interactive=False, show_download_button=False, show_label=False)
                    next_to_step_3_btn = gr.Button(get_ui_text('modal_next_btn', 'en'), variant="primary")
                
                # Step 3: Start Tutoring
                with gr.Column(visible=False) as step_3_container:
                    modal_step3_header = gr.Markdown(f"## {get_ui_text('modal_step3_header', 'en')}")
                    modal_step3_subheader = gr.Markdown(get_ui_text('modal_step3_subheader', 'en'))
                    start_btn = gr.Button(get_ui_text('modal_start_btn', 'en'), variant="primary")

        # --- Event Handlers & Connections ---
        
        # Language change handler
        def update_ui_language(lang):
             return {
                language_state: lang,
                app_title: gr.update(value=f"# {get_ui_text('app_title', lang)}"),
                app_header: gr.update(value=get_ui_text('app_header', lang)),
                session_header: gr.update(value=f"### {get_ui_text('session_header', lang)}"),
                new_session_btn: gr.update(value=get_ui_text('new_session_btn', lang)),
                session_status_btn: gr.update(value=get_ui_text('refresh_status_btn', lang)),
                language_dropdown: gr.update(label=get_ui_text('language_label', lang)),
                session_info_display: gr.update(label=get_ui_text('session_status_label', lang)),
                upload_header: gr.update(value=f"### {get_ui_text('upload_header', lang)}"),
                file_upload: gr.update(label=get_ui_text('file_upload_label', lang)),
                upload_status: gr.update(label=get_ui_text('upload_status_label', lang)),
                setup_header: gr.update(value=f"### {get_ui_text('setup_header', lang)}"),
                load_index_btn: gr.update(value=get_ui_text('load_index_btn', lang)),
                create_index_btn: gr.update(value=get_ui_text('create_index_btn', lang)),
                setup_status: gr.update(label=get_ui_text('setup_status_label', lang)),
                conversation_header: gr.update(value=f"### {get_ui_text('conversation_header', lang)}"),
                chat_disclaimer_md: gr.update(value=f"*{get_ui_text('chat_disclaimer', lang)}*"),
                user_input: gr.update(label=get_ui_text('ask_question_label', lang), placeholder=get_ui_text('user_input_placeholder', lang)),
                send_btn: gr.update(value=get_ui_text('send_btn', lang)),
                reset_btn: gr.update(value=get_ui_text('reset_btn', lang)),
                clear_btn: gr.update(value=get_ui_text('clear_btn', lang)),
                # --- Modal Text Updates ---
                modal_step1_header: gr.update(value=f"## {get_ui_text('modal_step1_header', lang)}"),
                modal_step1_subheader: gr.update(value=f"### {get_ui_text('modal_step1_subheader', lang)}"),
                modal_step1_info: gr.update(value=get_ui_text('modal_step1_info', lang)),
                modal_step1_success_header: gr.update(value=f"### {get_ui_text('modal_step1_success_header', lang)}"),
                next_to_step_2_btn: gr.update(value=get_ui_text('modal_next_btn', lang)),
                modal_step2_header: gr.update(value=f"## {get_ui_text('modal_step2_header', lang)}"),
                modal_step2_subheader: gr.update(value=get_ui_text('modal_step2_subheader', lang)),
                modal_step2_detail: gr.update(value=get_ui_text('modal_step2_detail', lang)),
                next_to_step_3_btn: gr.update(value=get_ui_text('modal_next_btn', lang)),
                modal_step3_header: gr.update(value=f"## {get_ui_text('modal_step3_header', lang)}"),
                modal_step3_subheader: gr.update(value=get_ui_text('modal_step3_subheader', lang)),
                start_btn: gr.update(value=get_ui_text('modal_start_btn', lang)),
            }

        all_ui_outputs = [
            language_state, app_title, app_header, session_header, new_session_btn,
            session_status_btn, language_dropdown, session_info_display, status_display, progress_display,
            upload_header, file_upload, upload_status, setup_header, load_index_btn, create_index_btn,
            setup_status, conversation_header, chat_disclaimer_md, user_input,
            send_btn, reset_btn, clear_btn,
            # --- Modal Outputs ---
            modal_step1_header, modal_step1_subheader, modal_step1_info, modal_step1_success_header, next_to_step_2_btn,
            modal_step2_header, modal_step2_subheader, modal_step2_detail, next_to_step_3_btn,
            modal_step3_header, modal_step3_subheader, start_btn
        ]

        language_dropdown.change(
            fn=update_ui_language,
            inputs=[language_dropdown],
            outputs=all_ui_outputs
        ).then(
            fn=check_and_update_ui_state,
            inputs=[language_dropdown],
            outputs=[user_input, status_display, progress_display]
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
            inputs=[language_state],
            outputs=[chatbot, session_info_display, upload_status, setup_status]
        ).then(
            fn=check_and_update_ui_state,
            inputs=[language_state],
            outputs=[user_input, status_display, progress_display]
        )

        session_status_btn.click(
            get_session_status, outputs=[session_info_display]
        )

        # File upload and index creation
        file_upload.change(
            handle_file_upload_staging,
            inputs=[file_upload, language_state],
            outputs=[upload_status, load_index_btn, create_index_btn, matched_index_id, uploaded_files_state]
        ).then(
            fn=check_and_update_ui_state,
            inputs=[language_state],
            outputs=[user_input, status_display, progress_display]
        )

        create_index_btn.click(
            save_and_create_index,
            inputs=[uploaded_files_state, language_state],
            outputs=[setup_status]
        ).then(
            fn=check_and_update_ui_state,
            inputs=[language_state],
            outputs=[user_input, status_display, progress_display]
        )


        load_index_btn.click(
            handle_load_index_click,
            inputs=[matched_index_id, language_state],
            outputs=[setup_status]
        ).then(
            fn=check_and_update_ui_state,
            inputs=[language_state],
            outputs=[user_input, status_display, progress_display]
        ).then(
            fn=check_and_update_ui_state,
            inputs=[language_state],
            outputs=[user_input, status_display, progress_display]
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

        # Language change handler - updates UI state when language changes
        language_dropdown.change(
            fn=check_and_update_ui_state,
            inputs=[language_dropdown],
            outputs=[user_input, status_display, progress_display]
        )

        # Load initial session status when the app loads. The popup will appear on top.
        interface.load(
            fn=get_session_status, 
            inputs=None, 
            outputs=[session_info_display]
        ).then(
            fn=check_and_update_ui_state,
            inputs=[language_state],
            outputs=[user_input, status_display, progress_display]
        )

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
    

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Eagerly initialize a default TutorEngine on startup
        global current_session_id
        default_session_id = str(uuid.uuid4())
        current_session_id = default_session_id
        
        print(f"Application starting up. Creating default session: {default_session_id}")
        engine = TutorEngine(session_id=default_session_id)
        user_sessions[default_session_id] = engine
        
        # Initialize the engine in the background
        await engine.initialize_engine()
        
        yield
        
        # Clean up resources on shutdown
        print("Application shutting down. Cleaning up sessions.")
        user_sessions.clear()
    
    interface = create_gradio_interface()
    app = FastAPI(lifespan=lifespan)

    @app.get("/health")
    def health_check():
        return Response(status_code=200, content="OK")

    app = gr.mount_gradio_app(app, interface, path="/")
    port = int(os.getenv("PORT", 7860))
    
    print(f"Launching on 0.0.0.0:{port}")
    print("ጤ Health check endpoint available at /health")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()