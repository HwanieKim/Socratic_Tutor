#!/usr/bin/env python3
"""
Dialogue Generator Module

Handles Stage 2 logic:
- Socratic dialogue generation
- Context integration
- Response formatting with source attribution
"""

import os
import traceback
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.llms import ChatMessage, MessageRole


from . import config
from .models import(
    ReasoningTriplet, 
    ScaffoldingDecision, 
    EnhancedAnswerEvaluation, 
    SessionLearningProfile, 
    LearningLevel
)
from .prompts_template import get_adaptive_tutor_template, get_adaptive_strategy_instructions, get_scaffolding_prompt
from .i18n import get_ui_text

class DialogueGenerator:
    """Handles Socratic dialogue generation"""
    
    def __init__(self):
        self.llm_tutor = GoogleGenAI(
            model_name=config.GEMINI_MODEL_NAME,
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
    def generate_adaptive_socratic_dialogue(
        self,
        triplet: ReasoningTriplet,
        source_nodes: list,
        conversation_memory,
        answer_evaluation: EnhancedAnswerEvaluation,
        learning_profile: SessionLearningProfile,
        adaptive_strategy: str,
        language: str = "en"
    ) -> str:
        """
        Generate adaptive Socratic dialogue based on student's learning level and performance
        
        Args:
            triplet: ReasoningTriplet with expert knowledge
            source_nodes: Retrieved source nodes
            conversation_memory: Recent conversation history
            answer_evaluation: Enhanced evaluation results
            learning_profile: Current learning profile and level
            adaptive_strategy: Determined adaptive strategy
            language: Language for response
            
        Returns:
            str: Adaptive tutoring response
        """
        try: 
            print(f"[DEBUG] 🎯 Generating adaptive dialogue:")
            print(f"  - Level: {learning_profile.current_level.value}")
            print(f"  - Strategy: {adaptive_strategy}")
            print(f"  - Binary Eval: {answer_evaluation.binary_evaluation}")
            print(f"  - Overall Score: {answer_evaluation.overall_score:.3f}")
            

            # context information format
            conversation_context = self._format_memory_context(conversation_memory)
            context_snippet,source_info = self._extract_context_info(source_nodes)
            user_input = self._get_last_user_input(conversation_memory)

            # prompt enhancement based on learning level
            level_enhancement = self._get_level_prompt_enhancement(learning_profile.current_level, language)
            strategy_instructions = get_adaptive_strategy_instructions(adaptive_strategy) 
            level_description = learning_profile.get_level_description()
            recent_performance = self._format_recent_performance(learning_profile)


            adaptive_template = get_adaptive_tutor_template(language)

            formatted_prompt = adaptive_template.format(
                #learning context
                current_level=learning_profile.current_level.value,
                level_description=level_description,
                recent_performance=recent_performance,
                adaptive_strategy=adaptive_strategy,
                strategy_instructions=strategy_instructions,

                #evaluation context 
                binary_evaluation=answer_evaluation.binary_evaluation,
                overall_score = f"{answer_evaluation.overall_score:.3f}",
                strengths = ", ".join(answer_evaluation.strengths) if answer_evaluation.strengths else "None identified",
                misconceptions = ", ".join(answer_evaluation.misconceptions) if answer_evaluation.misconceptions else "None identified",
                feedback = answer_evaluation.feedback,

                #expert knowledge context
                original_question=triplet.question,
                expert_reasoning_chain = triplet.reasoning_chain,
                expert_answer = triplet.answer,

                #context snippet
                conversation_context=conversation_context,
                context_snippet=context_snippet,
                source_info=source_info,
                user_input = user_input
                )

            enhanced_prompt = f"{formatted_prompt}\n\n{level_enhancement}"
            response = self.llm_tutor.complete(enhanced_prompt)
            response_text = response.text.strip()

            return response_text
        except Exception as e:
            print (f"[ERROR] Adaptive dialogue generation failed: {e}")
            if not answer_evaluation:
                return self._get_new_question_fallback(language)
            else:
                return self._fallback_response(triplet, answer_evaluation, language)  
    
    def generate_scaffolding_response(
            self,
            triplet: ReasoningTriplet,
            source_nodes: list, 
            conversation_memory,
            scaffolding_decision: ScaffoldingDecision,
            language:str = "en"
    )-> str:
        try:
            print(f"[DEBUG] generating scaffolding response with strategy : {scaffolding_decision.scaffold_strategy}")

            conversation_context = self._format_memory_context(conversation_memory)
            context_snippet, source_info = self._extract_context_info(source_nodes)
            user_input = self._get_last_user_input(conversation_memory)
            last_tutor_question = self._get_last_tutor_question(conversation_memory)

            scaffolding_template = get_scaffolding_prompt(language)
            formatted_prompt = scaffolding_template.format(
                context_snippet=context_snippet,
                source_info=source_info,
                tutor_question=last_tutor_question,
                expert_answer=triplet.answer,
                user_input=user_input,
                scaffold_strategy=scaffolding_decision.scaffold_strategy,
                strategy_description=scaffolding_decision.strategy_description,
                conversation_context=conversation_context,
                stuck_level=scaffolding_decision.stuck_count
                )
            response = self.llm_tutor.complete(formatted_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[ERROR] Scaffolding response generation failed: {e}")
            traceback.print_exc()
            return get_ui_text("engine_step_by_step", language)
        

    def _format_recent_performance(self, learning_profile: SessionLearningProfile) -> str:
        if not learning_profile.recent_scores_history:
            return "No recent performance data available."
        
        recent_avg = sum(learning_profile.recent_scores_history) / len(learning_profile.recent_scores_history)
        latest_score = learning_profile.recent_scores_history[-1]

        trend_info = ""
        if learning_profile.consecutive_high_performance >= 2:
            trend_info = f" (📈 {learning_profile.consecutive_high_performance} consecutive strong responses)"
        elif learning_profile.consecutive_low_performance >= 2:
            trend_info = f" (📉 {learning_profile.consecutive_low_performance} consecutive challenges)"
        
        stability_info = f"Stability at current level: {learning_profile.level_stability_count} interactions"
        
        return f"Recent average: {recent_avg:.2f}, Latest: {latest_score:.2f}, Total interactions: {learning_profile.total_interactions}{trend_info}. {stability_info}"

    def _get_last_tutor_question(self, conversation_memory) -> str:
        try:
            recent_messages = conversation_memory.get_all()
            if recent_messages and recent_messages[-1].role == MessageRole.ASSISTANT:
                return recent_messages[-1].content
            return ""
        except Exception as e:
            print(f"[ERROR] Error getting last tutor question: {e}")
            return ""

    def _get_last_user_input(self, conversation_memory) -> str:
        try:
            recent_messages = conversation_memory.get_all()
            if recent_messages and recent_messages[-1].role == MessageRole.USER:
                return recent_messages[-1].content
            return ""
        except Exception as e:
            print(f"[ERROR] Error getting last user input: {e}")
            return ""
        
    
    def _extract_context_info(self, source_nodes: list) -> tuple:
        """
        Extract context snippet and source information from retrieved nodes
        
        Args:
            source_nodes: List of retrieved source nodes
            
        Returns:
            tuple: (context_snippet, source_info)
        """
        context_snippet = "No specific context snippet found."
        source_info = "the provided text"
        
        if source_nodes:
            try:
                # Get the top source node
                top_node = source_nodes[0]
                context_snippet = top_node.node.get_content()
                
                # Extract source information from metadata
                metadata = top_node.node.metadata
                file_path = metadata.get('file_name', 'the document')
                page_label = metadata.get('page_label', '')
                
                # Extract only filename without path
                import os
                file_name = os.path.basename(file_path) if file_path else 'the document'
                
                # Format source info with filename only
                if page_label:
                    source_info = f"page {page_label} of {file_name}"
                else:
                    source_info = f"in {file_name}"
                    
                # Truncate context if too long
                if len(context_snippet) > 500:
                    context_snippet = context_snippet[:500] + "..."
                    
            except Exception as e:
                print(f"Error extracting context info: {e}")
        
        return context_snippet, source_info
    
    def _format_memory_context(self, memory) -> str:
        """
        Format conversation history for prompt context
        
        Args:
            memory: ChatMemoryBuffer
            
        Returns:
            str: Formatted conversation history
        """
        try:
            recent_messages = memory.get_all()
            
            if not recent_messages:
                return "This is the start of our conversation."
            
            # Format recent messages (last 6 for context)
            history_parts = []
            for msg in recent_messages[-6:]:
                role = "Student" if msg.role == MessageRole.USER else "Tutor"
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                history_parts.append(f"{role}: {content}")
            
            return "\n".join(history_parts)
            
        except Exception as e:
            print(f"Error formatting memory context: {e}")
            return "Previous conversation context unavailable."

    def _get_new_question_fallback(self, language: str) -> str:
        """
        Fallback response for new questions when generation fails
        """
        fallback_messages = {
        "en": "I'd like to help you explore this topic. Let's start by thinking about what you already know. What comes to mind when you think about this concept?",
        "it": "Vorrei aiutarti a esplorare questo argomento. Iniziamo pensando a quello che già sai. Cosa ti viene in mente quando pensi a questo concetto?",
        "es": "Me gustaría ayudarte a explorar este tema. Empecemos pensando en lo que ya sabes. ¿Qué te viene a la mente cuando piensas en este concepto?"
    }
    
        return fallback_messages.get(language, fallback_messages["en"])
    
    # 🎯 FIX FALLBACK METHOD SIGNATURE - Make it more flexible
    def _fallback_response(self, triplet: ReasoningTriplet, answer_evaluation, language: str = "en") -> str:
        """Generate fallback response - handles both AnswerEvaluation and EnhancedAnswerEvaluation"""
        try:
            # Handle both evaluation types
            if isinstance(answer_evaluation, EnhancedAnswerEvaluation):
                level = LearningLevel.L2_STRUCTURED_COMPREHENSION  # Default level for fallback
                # Use existing logic...
            else:
                # Legacy AnswerEvaluation handling
                response_messages = {
                    "en": {
                        "correct": "Excellent! You've grasped the key concept. Let's explore this topic further.",
                        "partially_correct": "You're on the right track! Let's build on what you've said.",
                        "incorrect": "Let's approach this from a different angle.",
                        "default": "I'd like to help you explore this topic."
                    }, 
                    "it": {
                    "correct": "Ottimo lavoro! Esploriamo ulteriormente questo argomento.",
                    "partially_correct": "Stai facendo buoni progressi! Costruiamo su quello che hai capito.",
                    "incorrect": "Approciamoci da un angolo diverso. Cosa pensi che potrebbe essere importante qui?",
                    "unclear": "Vedo la tua risposta. Lascia che ti guidi attraverso questo passo dopo passo."
                    }
                }
                
                messages = response_messages.get(language, response_messages["en"])
                binary_eval =getattr(answer_evaluation, 'evaluation', 'unclear')
                return messages.get(binary_eval, messages["default"])
        except Exception as e:
            print(f"Fallback response error: {e}")
            return "I'm here to help you learn. What would you like to explore?"
    
    
    
    
    
    
    def _get_level_prompt_enhancement(self, level: LearningLevel, language: str = "en") -> str:
        """Get level-specific prompt enhancement instructions"""
        
        level_enhancements = {
            "en": {
                LearningLevel.L0_PRE_CONCEPTUAL: """
**LEVEL-SPECIFIC GUIDANCE (L0 - Pre-Conceptual):**
- Use the simplest possible language and avoid jargon
- Break concepts into very basic, concrete parts
- Use everyday analogies and familiar examples
- Ask simple, direct questions with clear expectations
- Provide frequent encouragement and positive reinforcement
- Focus on building basic familiarity rather than deep understanding
- Example approach: "Think of this like [simple, familiar example]..."
""",
                
                LearningLevel.L1_FAMILIARIZATION: """
**LEVEL-SPECIFIC GUIDANCE (L1 - Familiarization):**
- Use clear, straightforward language
- Help build initial understanding of key concepts
- Ask questions that encourage basic connections
- Provide supportive guidance and encouragement
- Use concrete examples before abstract ones
- Focus on developing comfort with the topic
- Example approach: "Now that we've talked about X, what do you think about Y?"
""",
                
                LearningLevel.L2_STRUCTURED_COMPREHENSION: """
**LEVEL-SPECIFIC GUIDANCE (L2 - Structured Comprehension):**
- Help student see relationships and patterns
- Ask questions that reveal connections between concepts
- Support organized, systematic thinking
- Encourage students to explain their reasoning process
- Balance guidance with opportunities for independence
- Focus on building coherent understanding
- Example approach: "How do you think this connects to what we discussed earlier?"
""",
                
                LearningLevel.L3_PROCEDURAL_FLUENCY: """
**LEVEL-SPECIFIC GUIDANCE (L3 - Procedural Fluency):**
- Encourage confident application of knowledge
- Ask questions that challenge them to apply concepts in new ways
- Support development of systematic approaches
- Focus on building fluency and accuracy
- Encourage explaining methods and procedures
- Challenge them with variations and extensions
- Example approach: "You've got the process down well. How would you handle this variation?"
""",
                
                LearningLevel.L4_CONCEPTUAL_TRANSFER: """
**LEVEL-SPECIFIC GUIDANCE (L4 - Conceptual Transfer):**
- Challenge with complex, multi-layered questions
- Encourage application to completely new domains
- Support abstract reasoning and pattern recognition
- Ask questions that push boundaries of understanding
- Foster independent, creative problem-solving
- Encourage metacognitive reflection
- Example approach: "This principle could apply broadly. Where else might you see this pattern?"
"""
            },
            
            "it": {
                LearningLevel.L0_PRE_CONCEPTUAL: """
**GUIDA SPECIFICA PER LIVELLO (L0 - Pre-Concettuale):**
- Usa il linguaggio più semplice possibile ed evita il gergo
- Dividi i concetti in parti molto basilari e concrete
- Usa analogie quotidiane ed esempi familiari
- Fai domande semplici e dirette con aspettative chiare
- Fornisci incoraggiamento frequente e rinforzo positivo
- Concentrati sulla costruzione della familiarità di base
- Esempio di approccio: "Pensa a questo come [esempio semplice e familiare]..."
""",
                
                LearningLevel.L1_FAMILIARIZATION: """
**GUIDA SPECIFICA PER LIVELLO (L1 - Familiarizzazione):**
- Usa un linguaggio chiaro e diretto
- Aiuta a costruire la comprensione iniziale dei concetti chiave
- Fai domande che incoraggiano connessioni di base
- Fornisci guida e incoraggiamento di supporto
- Usa esempi concreti prima di quelli astratti
- Concentrati sullo sviluppo della comodità con l'argomento
- Esempio di approccio: "Ora che abbiamo parlato di X, cosa pensi di Y?"
""",
                
                LearningLevel.L2_STRUCTURED_COMPREHENSION: """
**GUIDA SPECIFICA PER LIVELLO (L2 - Comprensione Strutturata):**
- Aiuta lo studente a vedere relazioni e pattern
- Fai domande che rivelano connessioni tra concetti
- Supporta il pensiero organizzato e sistematico
- Incoraggia gli studenti a spiegare il loro processo di ragionamento
- Bilancia la guida con opportunità di indipendenza
- Concentrati sulla costruzione di comprensione coerente
- Esempio di approccio: "Come pensi che questo si colleghi a quello di cui abbiamo discusso prima?"
""",
                
                LearningLevel.L3_PROCEDURAL_FLUENCY: """
**GUIDA SPECIFICA PER LIVELLO (L3 - Fluidità Procedurale):**
- Incoraggia l'applicazione sicura della conoscenza
- Fai domande che li sfidano ad applicare concetti in modi nuovi
- Supporta lo sviluppo di approcci sistematici
- Concentrati sulla costruzione di fluidità e precisione
- Incoraggia la spiegazione di metodi e procedure
- Sfidali con variazioni ed estensioni
- Esempio di approccio: "Hai capito bene il processo. Come gestiresti questa variazione?"
""",
                
                LearningLevel.L4_CONCEPTUAL_TRANSFER: """
**GUIDA SPECIFICA PER LIVELLO (L4 - Trasferimento Concettuale):**
- Sfida con domande complesse e multi-livello
- Incoraggia l'applicazione a domini completamente nuovi
- Supporta il ragionamento astratto e il riconoscimento di pattern
- Fai domande che spingono i confini della comprensione
- Favorisci la risoluzione di problemi indipendente e creativa
- Incoraggia la riflessione metacognitiva
- Esempio di approccio: "Questo principio potrebbe applicarsi ampiamente. Dove altro potresti vedere questo pattern?"
"""
            }
        }
        
        enhancements = level_enhancements.get(language, level_enhancements["en"])
        return enhancements.get(level, enhancements[LearningLevel.L2_STRUCTURED_COMPREHENSION])
    
    
    
    
    # def enhance_response_with_encouragement(self, response: str, evaluation: AnswerEvaluation = None, language:str = "en") -> str:
    #     """
    #     Add encouraging elements to the response
        
    #     Args:
    #         response: Base response
    #         evaluation: Optional answer evaluation
            
    #     Returns:
    #         str: Enhanced response with encouragement
    #     """
    #     if not evaluation:
    #         return response
        
    #     encouragement_starters = {
    #     "en": {
    #         "correct": ["Excellent!", "Great thinking!", "Perfect!", "Well done!"],
    #         "partially_correct": ["Good start!", "You're on track!", "Nice thinking!", "Good insight!"],
    #         "incorrect": ["Let's explore this!", "Good effort!", "Let's think differently!", "Interesting perspective!"]
    #     },
    #     "it": {
    #         "correct": ["Eccellente!", "Ottimo ragionamento!", "Perfetto!", "Ben fatto!"],
    #         "partially_correct": ["Buon inizio!", "Sei sulla strada giusta!", "Buon ragionamento!", "Buona intuizione!"],
    #         "incorrect": ["Esploriamo questo!", "Buon tentativo!", "Pensiamo diversamente!", "Prospettiva interessante!"]
    #     }}
    #     starters = encouragement_starters.get(language, encouragement_starters["en"])
    
    #     # Add appropriate encouragement
    #     if evaluation.evaluation in starters:
    #         starter_options = starters[evaluation.evaluation]
    #     # Check if encouragement already exists
    #         if not any(starter.lower() in response.lower() for starter in starter_options):
    #             import random
    #             starter = random.choice(starter_options)
    #             response = f"{starter} {response}"
        
    #     return response
    
    # # LEGACY CODE
    # def generate_socratic_dialogue(

    #     self, 
    #     triplet: ReasoningTriplet, 
    #     source_nodes: list, 
    #     memory,
    #     answer_evaluation: AnswerEvaluation = None,
    #     scaffolding_decision: ScaffoldingDecision = None,
    #     language: str = "en"
    # ) -> str:
    #     """
    #     Stage 2: Generate Socratic dialogue response
        
    #     Args:
    #         triplet: Expert reasoning triplet
    #         source_nodes: Retrieved source documents
    #         memory: Conversation history
    #         answer_evaluation: Optional evaluation of student's answer
    #         scaffolding_decision: Optional scaffolding decision for struggling students
            
    #     Returns:
    #         str: Generated tutor response
    #     """
    #     try:
    #         # Extract context and source information
    #         context_snippet, source_info = self._extract_context_info(source_nodes)
            
    #         # Get conversation history
    #         conversation_context = self._format_memory_context(memory)
            
    #         # Get the user's latest input
    #         recent_messages = memory.get_all()
    #         user_input = ""
    #         if recent_messages and recent_messages[-1].role == MessageRole.USER:
    #             user_input = recent_messages[-1].content
            
    #         # Prepare reasoning information
    #         full_reasoning_chain = triplet.reasoning_chain if triplet else "No specific reasoning available."
            
    #         # Handle scaffolding decision (overrides answer evaluation for meta questions)
    #         if scaffolding_decision:
    #             # Use scaffolding decision metadata to guide LLM generation
    #             evaluation_data = {
    #                 "evaluation": "scaffolding_request",
    #                 "scaffold_type": scaffolding_decision.scaffold_type,
    #                 "stuck_level": scaffolding_decision.stuck_level,
    #                 "reason": scaffolding_decision.reason,
    #                 "feedback": f"Generate {scaffolding_decision.scaffold_type} scaffolding at level {scaffolding_decision.stuck_level}"
    #             }
    #             print(f"DEBUG: Dialogue Generator - Using scaffolding: {scaffolding_decision.scaffold_type} (level {scaffolding_decision.stuck_level})", flush=True)
    #         elif answer_evaluation:
    #             # Use provided answer evaluation
    #             evaluation_data = answer_evaluation.model_dump()
    #             print(f"DEBUG: Dialogue Generator - Using evaluation: {answer_evaluation.evaluation}", flush=True)
    #         else:
    #             # Default for new questions - no formal evaluation needed
    #             evaluation_data = {
    #                 "evaluation": "new_question",
    #                 "feedback": "This is the first turn."
    #             }
    #             print("DEBUG: Dialogue Generator - Using new question mode", flush=True)
            
    #         tutor_template = get_tutor_template(language)
    #         # Create tutor prompt
    #         tutor_prompt = tutor_template.format(
    #             context_snippet=context_snippet,
    #             source_info=source_info,
    #             reasoning_step=full_reasoning_chain,
    #             conversation_context=conversation_context,
    #             user_input=user_input,
    #             answer_evaluation_json=str(evaluation_data)
    #         )
            
    #         # Generate response
    #         response = self.llm_tutor.complete(tutor_prompt)
    #         return response.text.strip()
            
    #     except Exception as e:
    #         print(f"Dialogue generation error: {e}")
    #         # For new questions, don't use fallback that might trigger scaffolding
    #         if not answer_evaluation:
    #             return self._get_new_question_fallback(language)
    #         else:
    #             return self._fallback_response(triplet, answer_evaluation, language)
   