"""
Centralized Text Resources for Internalization (i18n)

This file contains all the strings used for gradio ui.

supported languages:
- English (default)
- Italian/italiano
"""

UI_TEXTS={
    "en":{
        "language_name": "English",
        "app_title": "Socratic Tutor",
        "app_header": "Upload your PDF documents and engage in intelligent tutoring sessions.",
        "lang_label": "Language",
        "session_header": "## Session Management",
        "new_session_btn": "New Session",
        "refresh_status_btn": "Refresh Status",
        "session_status_label": "Session Status",
        "upload_header": "## Step 1: Upload Documents",
        "file_upload_label": "Upload PDF Documents",
        "upload_status_label": "Upload Status",
        "setup_header": "## Setup",
        "load_index_btn": "Step 2: Load Detected Index",
        "create_index_btn": "Step 2: Create Index & Initialize Engine",
        "setup_status_label": "Setup Status",
        "conversation_header": "## Step 3: Conversation with Tutor",
        "chat_disclaimer": "Note: Tutoring conversation is only available in English.",
        "ask_question_label": "Ask a question (in English)",
        "send_btn": "Send",
        "reset_btn": "Reset Conversation",
        "clear_btn": "Clear Chat",
        "no_files_staged": "No files staged. Upload some files to begin.",
        "session_error": "Session error. Please start a new session.",
        "file_not_found_error": "Error: Staged file not found. Please re-upload.",
        "files_staged_msg": "file(s) are staged and ready:",
        "existing_index_found": "✅ Existing index found that matches these files. You can load it directly.",
        "no_index_found": "ℹ️ No matching index found. A new index will be created from these files.",
        "engine_not_ready": "Engine not ready. Please upload and index documents first.",
        "user_input_placeholder": "Type your question here..."
    },
    "it": {
        "language_name": "Italiano",
        "app_title": "Tutore Socratico",
        "app_header": "Carica i tuoi documenti PDF e avvia sessioni di tutoraggio intelligenti.",
        "lang_label": "Lingua",
        "session_header": "## Gestione Sessione",
        "new_session_btn": "Nuova Sessione",
        "refresh_status_btn": "Aggiorna Stato",
        "session_status_label": "Stato Sessione",
        "upload_header": "## Passo 1: Carica Documenti",
        "file_upload_label": "Carica Documenti PDF",
        "upload_status_label": "Stato Caricamento",
        "setup_header": "## Configurazione",
        "load_index_btn": "Passo 2: Carica Indice Rilevato",
        "create_index_btn": "Passo 2: Crea Indice e Inizializza Sistema",
        "setup_status_label": "Stato Configurazione",
        "conversation_header": "## Passo 3: Conversazione con il Tutore",
        "chat_disclaimer": "Nota: Al momento la conversazione di tutoraggio è disponibile solo in inglese.",
        "ask_question_label": "Fai una domanda (in inglese)",
        "send_btn": "Invia",
        "reset_btn": "Resetta Conversazione",
        "clear_btn": "Pulisci Chat",
        "no_files_staged": "Nessun file in preparazione. Carica dei file per iniziare.",
        "session_error": "Errore di sessione. Si prega di iniziare una nuova sessione.",
        "file_not_found_error": "Errore: File in preparazione non trovato. Si prega di ricaricare.",
        "files_staged_msg": "file in preparazione e pronti:",
        "existing_index_found": "✅ Trovato indice esistente che corrisponde a questi file. Puoi caricarlo direttamente.",
        "no_index_found": "ℹ️ Nessun indice corrispondente trovato. Verrà creato un nuovo indice da questi file.",
        "engine_not_ready": "Sistema non pronto. Si prega di caricare e indicizzare prima i documenti.",

        "user_input_placeholder": "Scrivi qui la tua domanda..."
    }
}

def get_ui_text(key:str, lang:str="en") -> str:
    """
    Get UI text for the specified key and language. 
    
    Args:
        key (str): The key for the UI text.
        lang (str): The language code (default is "en").
        
    Returns:
        str: The localized UI text.
    """
    return UI_TEXTS.get(lang, UI_TEXTS["en"]).get(key, UI_TEXTS["en"].get(key, f"<{key}_NOT_FOUND>"))