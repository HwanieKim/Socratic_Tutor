"""
Centralized Text Resources for Internalization (i18n)

This file contains all the strings used for gradio ui.

supported languages:
- English (default)  
- Italian/italiano
"""

UI_TEXTS = {
    "en": {
        "language_name": "English",
        # Main UI
        "app_title": "Socratic Tutor",
        "app_header": "Upload your PDF documents and engage in intelligent tutoring sessions.",
        "language_label": "Language",
        
        # Session Management
        "session_header": "Session Management", 
        "new_session_btn": "New Session",
        "refresh_status_btn": "Refresh Status",
        "session_status_label": "Session Status",
        
        # File Upload
        "upload_header": "Step 1: Upload Documents",
        "file_upload_label": "Upload PDF Documents",
        "upload_status_label": "Upload Status",
        
        # Setup
        "setup_header": "Setup",
        "load_index_btn": "Step 2: Load Detected Index", 
        "create_index_btn": "Step 2: Create Index & Initialize Engine",
        "setup_status_label": "Setup Status",
        
        # Conversation
        "conversation_header": "Step 3: Conversation with Tutor",
        "chat_disclaimer": "Note: Tutoring conversation is only available in English.",
        "ask_question_label": "Ask a question (in English)",
        "send_btn": "Send",
        "reset_btn": "Reset Conversation", 
        "clear_btn": "Clear Chat",
        
        # File handling messages
        "no_files_staged": "No files staged. Upload some files to begin.",
        "session_error": "Session error. Please start a new session.",
        "file_not_found_error": "Error: Staged file not found. Please re-upload.",
        "files_staged": "{count} file(s) are staged and ready:\n{filenames}",
        "existing_index_found": "✅ Existing index found that matches these files. You can load it directly.",
        "no_index_found": "ℹ️ No matching index found. A new index will be created from these files.",
        "engine_not_ready": "Engine not ready. Please upload and index documents first.",
        "user_input_placeholder": "Type your question here...",
        
        # Modal texts
        "modal_step1_header": "Step 1: Upload Your Documents",
        "modal_step1_subheader": "Drag & Drop or Click to Upload", 
        "modal_step1_info": "Once uploaded, you will see a status update like this:",
        "modal_step1_success_header": "Upload Success",
        "modal_next_btn": "Next Step",
        "modal_step2_header": "Step 2: Let the Socratic Tutor learn your documents",
        "modal_step2_subheader": "After successful uploading, click the 'Create New Index' button that appears.",
        "modal_step2_detail": "The process may take a few minutes depending on the document size. You will see a completion status when it's done.",
        "modal_step3_header": "Step 3: Start Your Tutoring Session!",
        "modal_step3_subheader": "Everything is ready! Start asking questions in the chat window.",
        "modal_start_btn": "Let's Get Started!",
        
        # Index creation
        "no_files_staged_for_creation": "No files staged for index creation. Please upload files first.",
        "index_creation_step1": "Step 1/2: Saving files to permanent storage...",
        "index_creation_step2": "Step 2/2: Creating new index from files...",
        "index_creation_failed": "Index creation failed",
        
        # Session status
        "no_active_session": "No active session",
        "session_not_found": "Session not found",
        "error_prefix": "Error",
        "session_id_prefix": "Session ID",
        "documents_prefix": "Documents", 
        "documents_uploaded_suffix": "uploaded",
        "documents_indexed_suffix": "indexed",
        "engine_status_prefix": "Engine Status",
        "engine_ready": "Ready",
        "engine_not_ready": "Not Ready",
        "created_at_prefix": "Created",
        "unknown": "Unknown", 
        "session_status_error": "Error retrieving session status",
        "session_created": "New session created: {session_id}...",
        "conversation_reset": "Conversation has been reset",
        "index_load_success": "✅ Index loaded successfully. Ready for tutoring!",
        "index_load_error": "Failed to load index",
        
        # Chat controls
        "chat_disabled_step1": "📝 Please complete Step 1: Upload your documents first",
        "chat_disabled_step2": "⚙️ Please complete Step 2: Create index from your documents", 
        "chat_enabled_ready": "type your question here...",
        "system_not_ready": "The tutoring system is not ready. Please ensure both steps are completed.",
        "chat_error": "I'm having trouble processing your message right now. Please try again.",
        
        # Tutorial messages
        "tutorial_step1_title": "Step 1: Upload Documents",
        "tutorial_step1_desc": "Upload your PDF documents to begin",
        "tutorial_step2_title": "Step 2: Create Index",
        "tutorial_step2_desc": "Process your documents for intelligent tutoring", 
        "tutorial_step3_title": "Step 3: Start Learning",
        "tutorial_step3_desc": "Ask questions and engage with your AI tutor",
        
        # Messages for gradio_ui_railway.py
        "upload_documents_first": "📝: Please upload your documents first to get started with tutoring.\n\n💡 Upload PDF files using the file upload area in the sidebar.",
        "create_index_first": "⚙️: Please create an index from your uploaded documents before starting tutoring.\n\n💡 Click the 'Create Index' button after uploading your documents.",
        
        # TutorEngine messages
        "engine_upload_documents_first": "📝: Please upload your documents first to get started with tutoring.\n\n💡 Upload PDF files using the file upload area in the sidebar.",
        "engine_create_index_first": "⚙️: Please create an index from your uploaded documents before starting tutoring.\n\n💡 Click the 'Create Index' button after uploading your documents.",
        "engine_system_not_ready": "🚫 The tutoring system is not ready. Please ensure both steps are completed.",
        "engine_index_not_loaded": "⚠️ Tutor Engine is not ready. Please ensure an index has been created and loaded successfully.",
        "engine_happy_to_help": "😊 I'd be happy to help! Please ask me a question about your documents.",
        "engine_question_too_long": "📝 Your question is quite long. Could you please break it down into smaller, more specific questions?",
        "engine_high_demand": "⏳ I'm experiencing high demand right now, which may cause delays. Please wait a moment and try your question again.",
        "engine_connection_error": "🌐 I'm having trouble connecting. Please check your internet connection and try again.",
        "engine_unexpected_error": "❌ An unexpected error occurred. Please try again.",
        "engine_insufficient_knowledge": "🤔 I apologize, but I don't have sufficient information about this topic in my knowledge base. Could you try asking about something else, or provide more context?",
        "engine_processing_error": "⚠️ I'm having trouble processing your question right now. Could you try rephrasing it?",
        "engine_follow_up_no_context": "🔄 I don't have the context from our previous conversation. Let's start fresh with your question.",
        "engine_interesting_response": "🤔 That's an interesting response! Let's explore it further. What led you to that thinking?",
        "engine_continue_discussion": "Let's continue our discussion. What would you like to explore about this topic?",
        "engine_step_by_step": "I'm here to help! Let's think about this step by step. What aspect would you like to focus on first?",
        "engine_no_files": "📂 No files found. Please upload some documents first.",
        "engine_index_not_found": "📁 Index not found. Please create an index first.",
        "engine_index_path_missing": "⚠️ Index path is missing. Please check your configuration.",
        "engine_upload_success_simple": "✅ Documents uploaded successfully!",
        "engine_upload_failed_simple": "❌ Upload failed.",
        "engine_no_new_docs": "ℹ️ No new documents were saved as they already exist.",
        "engine_load_success": "✅ Loaded index with {count} documents. Ready for tutoring!",
        "engine_load_failed": "❌ Failed to load index: {error}.",
        
        # 👇 [추가] 누락된 키들
        "engine_load_success_simple": "✅ Index loaded successfully. Ready for tutoring!",
        "engine_index_path_not_found": "❌ Index path not found. Please check your configuration.",
        
        "engine_index_creation_start": "Creating index from {count} documents...",
        "engine_index_updating_db": "Updating database to mark documents as indexed...",
        "engine_index_reloading": "Reloading the engine with new index...",
        "engine_index_initializing_modules": "Initializing modules...",
        "engine_index_creation_success": "✅ Index created successfully!\n• Processed {count} documents\n• Engine ready for tutoring",
        "engine_index_creation_failed": "❌ Index creation failed: {error}",
        
        # Learning Insights - 누락된 키들 추가
        "learning_insights_header": "📊 Learning Session Insights",
        "learning_insights_btn": "Show Learning Insights",
        "current_level_label": "Current Level",
        "level_description_label": "Description",
        "total_interactions_label": "Total Interactions",
        "session_duration_label": "Session Duration",
        "recent_performance_header": "📈 Recent Performance",
        "average_score_label": "Average Score",
        "latest_score_label": "Latest Score",
        "performance_trend_label": "Trend",
        "evaluations_count_label": "Evaluations",
        "level_progression_header": "🔄 Level Progression",
        "last_level_change_label": "Latest Level Change",
        "total_level_changes_label": "Total Changes",
        "performance_streaks_header": "🎯 Performance Streaks",
        "consecutive_high_label": "Consecutive High Performance",
        "consecutive_low_label": "Consecutive Low Performance",
        "stability_at_level_label": "Stability at Current Level",
        "no_performance_data": "No recent performance data available",
        "no_level_changes": "No level changes yet",
        "minutes_unit": "minutes",
        "trend_improving": "Improving",
        "trend_declining": "Declining", 
        "trend_stable": "Stable",
        "trend_insufficient_data": "Insufficient Data",
        "insights_error": "Error loading insights",
        
    },
    "it": {
        "language_name": "Italiano",
        # Main UI
        "app_title": "Tutore Socratico",
        "app_header": "Carica i tuoi documenti PDF e avvia sessioni di tutoraggio intelligenti.",
        "language_label": "Lingua",
        
        # Session Management  
        "session_header": "Gestione Sessione",
        "new_session_btn": "Nuova Sessione",
        "refresh_status_btn": "Aggiorna Stato",
        "session_status_label": "Stato Sessione",
        
        # File Upload
        "upload_header": "Passo 1: Carica Documenti",
        "file_upload_label": "Carica Documenti PDF",
        "upload_status_label": "Stato Caricamento",
        
        # Setup
        "setup_header": "Configurazione",
        "load_index_btn": "Passo 2: Carica Indice Rilevato",
        "create_index_btn": "Passo 2: Crea Indice e Inizializza Sistema",
        "setup_status_label": "Stato Configurazione",
        
        # Conversation
        "conversation_header": "Passo 3: Conversazione con il Tutore",
        "chat_disclaimer": "Nota: Al momento la conversazione di tutoraggio è disponibile solo in inglese.",
        "ask_question_label": "Fai una domanda (in inglese)",
        "send_btn": "Invia",
        "reset_btn": "Resetta Conversazione",
        "clear_btn": "Pulisci Chat",
        
        # File handling messages
        "no_files_staged": "Nessun file in preparazione. Carica dei file per iniziare.",
        "session_error": "Errore di sessione. Si prega di iniziare una nuova sessione.",
        "file_not_found_error": "Errore: File in preparazione non trovato. Si prega di ricaricare.",
        "files_staged": "{count} file sono in preparazione e pronti:\n{filenames}",
        "existing_index_found": "✅ Trovato indice esistente che corrisponde a questi file. Puoi caricarlo direttamente.",
        "no_index_found": "ℹ️ Nessun indice corrispondente trovato. Verrà creato un nuovo indice da questi file.",
        "engine_not_ready": "Sistema non pronto. Si prega di caricare e indicizzare prima i documenti.",
        "user_input_placeholder": "Scrivi qui la tua domanda...",
        
        # Modal texts
        "modal_step1_header": "Passo 1: Carica i Tuoi Documenti",
        "modal_step1_subheader": "Trascina e Rilascia o Clicca per Caricare",
        "modal_step1_info": "Una volta caricato, vedrai un aggiornamento di stato come questo:",
        "modal_step1_success_header": "Caricamento Riuscito",
        "modal_next_btn": "Passo Successivo",
        "modal_step2_header": "Passo 2: Lascia che il Tutore Socratico impari i tuoi documenti",
        "modal_step2_subheader": "Dopo il caricamento, clicca sul pulsante 'Crea Nuovo Indice' che appare.",
        "modal_step2_detail": "Il processo potrebbe richiedere alcuni minuti. Vedrai uno stato di completamento quando avrà finito.",
        "modal_step3_header": "Passo 3: Inizia la Tua Sessione di Tutoraggio!",
        "modal_step3_subheader": "Tutto è pronto! Inizia a fare domande nella finestra di chat.",
        "modal_start_btn": "Iniziamo!",
        
        # Index creation
        "no_files_staged_for_creation": "Nessun file in preparazione per la creazione dell'indice. Si prega di caricare prima i file.",
        "index_creation_step1": "Passo 1/2: Salvataggio dei file nell'archivio permanente...",
        "index_creation_step2": "Passo 2/2: Creazione di un nuovo indice dai file...",
        "index_creation_failed": "Creazione dell'indice non riuscita",
        
        # Session status
        "no_active_session": "Nessuna sessione attiva",
        "session_not_found": "Sessione non trovata",
        "error_prefix": "Errore",
        "session_id_prefix": "ID Sessione",
        "documents_prefix": "Documenti",
        "documents_uploaded_suffix": "caricati",
        "documents_indexed_suffix": "indicizzati",
        "engine_status_prefix": "Stato Sistema",
        "engine_ready": "Pronto",
        "engine_not_ready": "Non Pronto",
        "created_at_prefix": "Creato",
        "unknown": "Sconosciuto",
        "session_status_error": "Errore nel recuperare lo stato della sessione",
        "session_created": "Nuova sessione creata: {session_id}...",
        "conversation_reset": "La conversazione è stata ripristinata",
        "index_load_success": "✅ Indice caricato con successo. Pronto per il tutoraggio!",
        "index_load_error": "Caricamento dell'indice non riuscito",
        
        # Chat controls
        "chat_disabled_step1": "📝 Si prega di completare il Passo 1: Caricare prima i documenti",
        "chat_disabled_step2": "⚙️ Si prega di completare il Passo 2: Creare l'indice dai documenti",
        "chat_enabled_ready": "inserisci qui la tua domanda...",
        "system_not_ready": "Il sistema di tutoraggio non è pronto. Assicurati che entrambi i passaggi siano completati.",
        "chat_error": "Sto avendo problemi nell'elaborare il tuo messaggio. Si prega di riprovare.",
        
        # Tutorial messages
        "tutorial_step1_title": "Passo 1: Caricare Documenti",
        "tutorial_step1_desc": "Carica i tuoi documenti PDF per iniziare",
        "tutorial_step2_title": "Passo 2: Creare Indice",
        "tutorial_step2_desc": "Elabora i tuoi documenti per il tutoraggio intelligente",
        "tutorial_step3_title": "Passo 3: Inizia ad Imparare",
        "tutorial_step3_desc": "Fai domande e interagisci con il tuo tutore AI",
        
        # Messages for gradio_ui_railway.py
        "upload_documents_first": "📝: Si prega di caricare prima i documenti per iniziare il tutoraggio.\n\n💡 Carica i file PDF utilizzando l'area di caricamento nella barra laterale.",
        "create_index_first": "⚙️: Si prega di creare un indice dai documenti caricati prima di iniziare il tutoraggio.\n\n💡 Clicca il pulsante 'Crea Indice' dopo aver caricato i tuoi documenti.",
        
        # TutorEngine messages
        "engine_upload_documents_first": "📝: Si prega di caricare prima i documenti per iniziare il tutoraggio.\n\n💡 Carica i file PDF utilizzando l'area di caricamento nella barra laterale.",
        "engine_create_index_first": "⚙️: Si prega di creare un indice dai documenti caricati prima di iniziare il tutoraggio.\n\n💡 Clicca il pulsante 'Crea Indice' dopo aver caricato i tuoi documenti.",
        "engine_system_not_ready": "🚫 Il sistema di tutoraggio non è pronto. Assicurati che entrambi i passaggi siano completati.",
        "engine_index_not_loaded": "⚠️ Il Tutore non è pronto. Assicurati che un indice sia stato creato e caricato con successo.",
        "engine_happy_to_help": "😊 Sarò felice di aiutarti! Fai una domanda sui tuoi documenti.",
        "engine_question_too_long": "📝 La tua domanda è piuttosto lunga. Potresti suddividerla in domande più piccole e specifiche?",
        "engine_high_demand": "⏳ Sto sperimentando un'alta domanda in questo momento, che potrebbe causare ritardi. Aspetta un momento e riprova la tua domanda.",
        "engine_connection_error": "🌐 Sto avendo problemi di connessione. Controlla la connessione internet e riprova.",
        "engine_unexpected_error": "❌ Si è verificato un errore imprevisto. Riprova.",
        "engine_insufficient_knowledge": "🤔 Mi dispiace, ma non ho informazioni sufficienti su questo argomento nella mia base di conoscenze. Potresti provare a chiedere qualcos'altro o fornire più contesto?",
        "engine_processing_error": "⚠️ Sto avendo problemi nell'elaborare la tua domanda. Potresti provare a riformularla?",
        "engine_follow_up_no_context": "🔄 Non ho il contesto della nostra conversazione precedente. Iniziamo da capo con la tua domanda.",
        "engine_interesting_response": "🤔 È una risposta interessante! Esploriamola ulteriormente. Cosa ti ha portato a questo ragionamento?",
        "engine_continue_discussion": "Continuiamo la nostra discussione. Cosa vorresti esplorare su questo argomento?",
        "engine_step_by_step": "Sono qui per aiutarti! Pensiamo a questo passo dopo passo. Su quale aspetto vorresti concentrarti prima?",
        "engine_no_files": "📂 Nessun file trovato. Si prega di caricare prima alcuni documenti.",
        "engine_index_not_found": "📁 Indice non trovato. Si prega di creare prima un indice.",
        "engine_index_path_missing": "⚠️ Percorso dell'indice mancante. Si prega di controllare la configurazione.",
        "engine_upload_success_simple": "✅ Caricamento riuscito!",
        "engine_upload_failed_simple": "❌ Caricamento fallito.",
        "engine_no_new_docs": "ℹ️ Nessun nuovo documento da elaborare.",
        "engine_load_success": "✅ Indice caricato con {count} documenti. Pronto per il tutoraggio!",
        "engine_load_failed": "❌ Caricamento dell'indice non riuscito: {error}",
        
        # 👇 [추가] 누락된 키들 - 이탈리아어 번역
        "engine_load_success_simple": "✅ Indice caricato con successo. Pronto per il tutoraggio!",
        "engine_index_path_not_found": "❌ Percorso dell'indice non trovato. Si prega di controllare la configurazione.",
        
        "engine_index_creation_start": "Creando indice da {count} documenti...",
        "engine_index_updating_db": "Aggiornamento del database per contrassegnare i documenti come indicizzati...",
        "engine_index_reloading": "Ricaricamento del motore con il nuovo indice...",
        "engine_index_initializing_modules": "Inizializzazione dei moduli...",
        "engine_index_creation_success": "✅ Indice creato con successo!\n• Documenti elaborati: {count}\n• Motore pronto per il tutoraggio",
        "engine_index_creation_failed": "❌ Creazione dell'indice fallita: {error}",
        
        # Learning Insights - 이탈리아어
        "learning_insights_header": "📊 Insights della Sessione di Apprendimento",
        "learning_insights_btn": "Mostra Insights di Apprendimento",
        "current_level_label": "Livello Attuale",
        "level_description_label": "Descrizione",
        "total_interactions_label": "Interazioni Totali",
        "session_duration_label": "Durata Sessione",
        "recent_performance_header": "📈 Performance Recente",
        "average_score_label": "Punteggio Medio",
        "latest_score_label": "Ultimo Punteggio",
        "performance_trend_label": "Tendenza",
        "evaluations_count_label": "Valutazioni",
        "level_progression_header": "🔄 Progressione di Livello",
        "last_level_change_label": "Ultimo Cambio di Livello",
        "total_level_changes_label": "Cambi Totali",
        "performance_streaks_header": "🎯 Serie di Performance",
        "consecutive_high_label": "Performance Alta Consecutiva",
        "consecutive_low_label": "Performance Bassa Consecutiva", 
        "stability_at_level_label": "Stabilità al Livello Attuale",
        "no_performance_data": "Nessun dato di performance recente disponibile",
        "no_level_changes": "Nessun cambio di livello ancora",
        "minutes_unit": "minuti",
        "trend_improving": "In Miglioramento",
        "trend_declining": "In Declino",
        "trend_stable": "Stabile",
        "trend_insufficient_data": "Dati Insufficienti",
        "insights_error": "Errore nel caricamento degli insights",
        
    }
}

def get_ui_text(key: str, lang: str = "en") -> str:
    """
    Get UI text for the specified key and language.
    
    Args:
        key (str): The key for the UI text.
        lang (str): The language code (default is "en").
        
    Returns:
        str: The localized UI text.
    """
    return UI_TEXTS.get(lang, UI_TEXTS["en"]).get(key, UI_TEXTS["en"].get(key, f"<{key}_NOT_FOUND>"))
