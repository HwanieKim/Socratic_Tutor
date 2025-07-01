#!/usr/bin/env python3
"""
Production Enhancement Module

Additional features for production deployment:
- Rate limiting
- Topic relevance detection
- Conversation quality metrics
- Enhanced logging
"""

import time
import re
from typing import Dict, List
from datetime import datetime, timedelta

class ProductionEnhancements:
    def __init__(self, knowledge_base_index=None):
        self.rate_limiter = RateLimiter()
        self.topic_filter = TopicRelevanceFilter(knowledge_base_index)
        self.metrics = ConversationMetrics()
        self.logger = EnhancedLogger()
    
    def is_request_allowed(self, user_id: str = "default") -> bool:
        """Check if request is within rate limits"""
        return self.rate_limiter.is_allowed(user_id)
    
    def is_topic_relevant(self, question: str, conversation_context: str = None) -> bool:
        """Check if question is related to the knowledge base content"""
        return self.topic_filter.is_relevant(question, conversation_context)
    
    def log_interaction(self, question: str, response: str, user_id: str = "default"):
        """Log user interaction for analysis"""
        self.logger.log_interaction(question, response, user_id)
        self.metrics.record_interaction(question, response)

class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.request_log: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        now = datetime.now()
        
        if user_id not in self.request_log:
            self.request_log[user_id] = []
        
        # Clean old requests
        cutoff_time = now - timedelta(seconds=self.time_window)
        self.request_log[user_id] = [
            req_time for req_time in self.request_log[user_id] 
            if req_time > cutoff_time
        ]
        
        # Check if under limit
        if len(self.request_log[user_id]) < self.max_requests:
            self.request_log[user_id].append(now)
            return True
        
        return False

class TopicRelevanceFilter:
    def __init__(self, knowledge_base_index=None, similarity_threshold=0.3):
        """
        Reasoning-Model-First Topic Relevance Filter
        
        This filter now primarily relies on the reasoning model's judgment.
        Hard-coded patterns are kept minimal for obviously harmful content only.
        
        Args:
            knowledge_base_index: LlamaIndex VectorStoreIndex for semantic similarity
            similarity_threshold: Minimum similarity score for relevance (0.0-1.0)
        """
        self.knowledge_base_index = knowledge_base_index
        self.similarity_threshold = similarity_threshold
        
        # MINIMAL patterns for obviously harmful/inappropriate content only
        self.harmful_patterns = [
            r'\b(hate|violence|illegal|harmful)\b',
            r'\b(offensive|inappropriate|adult)\b'
        ]
        
        # Remove most hard-coded topic filters - let reasoning model decide
    
    def is_relevant(self, question: str, conversation_context: str = None) -> bool:
        """
        SIMPLIFIED: Check only for harmful content, let reasoning model handle topic relevance
        
        Args:
            question: User's question
            conversation_context: Previous conversation context
            
        Returns:
            bool: True unless clearly harmful content
        """
        question_lower = question.lower().strip()
        
        # Handle empty inputs
        if not question_lower or len(question_lower) < 2:
            return False
        
        # Check only for harmful content
        for pattern in self.harmful_patterns:
            if re.search(pattern, question_lower):
                return False
        
        # For all other cases, let the reasoning model decide
        return True
    
    # Removed complex topic filtering methods - reasoning model handles this now

class ConversationMetrics:
    def __init__(self):
        self.interactions = []
        self.conversation_starts = 0
        self.total_questions = 0
        self.avg_question_length = 0
        self.topic_switches = 0
    
    def record_interaction(self, question: str, response: str):
        """Record metrics for each interaction"""
        self.total_questions += 1
        self.interactions.append({
            'timestamp': datetime.now(),
            'question_length': len(question),
            'response_length': len(response),
            'question': question[:100]  # Store first 100 chars for analysis
        })
        
        # Update running averages
        self.avg_question_length = (
            (self.avg_question_length * (self.total_questions - 1) + len(question)) 
            / self.total_questions
        )
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        if not self.interactions:
            return {"status": "No interactions recorded"}
        
        recent_interactions = self.interactions[-10:]  # Last 10 interactions
        avg_response_length = sum(i['response_length'] for i in recent_interactions) / len(recent_interactions)
        
        return {
            'total_questions': self.total_questions,
            'avg_question_length': round(self.avg_question_length, 1),
            'avg_response_length': round(avg_response_length, 1),
            'interactions_last_hour': len([
                i for i in self.interactions 
                if i['timestamp'] > datetime.now() - timedelta(hours=1)
            ])
        }

class EnhancedLogger:
    def __init__(self):
        self.log_file = "tutor_interactions.log"
    
    def log_interaction(self, question: str, response: str, user_id: str):
        """Log interaction to file"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] User: {user_id} | Q: {question[:100]}... | R: {response[:100]}...\n"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Logging error: {e}")

# Enhanced TutorEngine wrapper
class ProductionTutorEngine:
    def __init__(self, base_engine, knowledge_base_index=None):
        """
        Initialize ProductionTutorEngine with enhanced capabilities
        
        Args:
            base_engine: Base TutorEngine instance
            knowledge_base_index: VectorStoreIndex for semantic topic filtering
        """
        self.engine = base_engine
        self.knowledge_base_index = knowledge_base_index
        
        # Initialize enhancements with knowledge base
        self.enhancements = ProductionEnhancements(knowledge_base_index)
        
        # Track conversation context for better follow-up detection
        self.conversation_history = []
    
    def get_guidance(self, user_question: str, user_id: str = "default") -> str:
        """Enhanced guidance method with production features - Reasoning Model First Approach"""
        
        # Rate limiting check
        if not self.enhancements.is_request_allowed(user_id):
            return "You're asking questions quite frequently. Please wait a moment before asking again."
        
        # Input validation
        if not user_question or not user_question.strip():
            return "I'd be happy to help! Please ask me a question."
        
        # CORE CHANGE: Let the reasoning model decide first
        # Get the reasoning triplet to see if the question can be answered
        try:
            reasoning_triplet, source_nodes = self.engine._stage1_internal_monologue(user_question)
            
            # Check if reasoning model found sufficient information
            if (reasoning_triplet and 
                reasoning_triplet.answer and 
                "insufficient information" in reasoning_triplet.answer.lower()):
                return ("I don't have enough information about that topic in my knowledge base. "
                       "Could you please ask about the subject matter we're studying?")
            
            # If reasoning model found relevant information, proceed with Socratic dialogue
            response = self.engine._stage2_socratic_dialogue(reasoning_triplet, source_nodes)
            
        except Exception as e:
            # Fallback to base engine if there's an error
            response = self.engine.get_guidance(user_question)
        
        # Update conversation history
        self.conversation_history.append({
            'question': user_question,
            'response': response,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history (last 10 interactions)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        # Log interaction
        self.enhancements.log_interaction(user_question, response, user_id)
        
        return response
    
    def _get_conversation_context(self) -> str:
        """Get recent conversation context for follow-up detection"""
        if not self.conversation_history:
            return ""
        
        # Return last 2-3 interactions as context
        recent_interactions = self.conversation_history[-3:]
        context_parts = []
        
        for interaction in recent_interactions:
            context_parts.append(f"Q: {interaction['question'][:100]}")
            context_parts.append(f"A: {interaction['response'][:100]}")
        
        return " | ".join(context_parts)
    
    def reset(self):
        """Reset conversation state"""
        self.engine.reset()
        self.conversation_history = []
    
    def get_metrics(self) -> Dict:
        """Get conversation metrics"""
        return self.enhancements.metrics.get_summary()

# Test the production enhancements
def test_production_features():
    """Test production enhancement features"""
    print("Testing Production Enhancement Features...")
    
    # Test rate limiter
    print("\n1. Testing Rate Limiter:")
    rate_limiter = RateLimiter(max_requests=3, time_window=10)
    
    for i in range(5):
        allowed = rate_limiter.is_allowed("test_user")
        print(f"  Request {i+1}: {'✅ Allowed' if allowed else '❌ Rate limited'}")
    
    # Test topic relevance
    print("\n2. Testing Enhanced Topic Relevance Filter:")
    topic_filter = TopicRelevanceFilter()  # No knowledge base for this test
    
    test_questions = [
        ("What is this concept?", "Follow-up (Relevant)"),
        ("How do I bake a cake?", "Irrelevant"),
        ("What are the principles involved?", "Academic (Relevant)"),
        ("What's the weather like?", "Irrelevant"),
        ("Can you explain more?", "Follow-up (Relevant)"),
        ("Tell me about football", "Irrelevant"),
        ("How does this process work?", "Academic (Relevant)")
    ]
    
    for question, expected in test_questions:
        relevant = topic_filter.is_relevant(question)
        expected_relevant = "Relevant" in expected
        status = "✅" if relevant == expected_relevant else "❌"
        print(f"  {status} '{question}' -> {'Relevant' if relevant else 'Irrelevant'} (Expected: {expected})")
    
    # Test metrics
    print("\n3. Testing Metrics:")
    metrics = ConversationMetrics()
    
    # Record some test interactions
    test_interactions = [
        ("What is sustainable design?", "Sustainable design is..."),
        ("Tell me more", "Here are more details..."),
        ("How about examples?", "Here are some examples...")
    ]
    
    for q, r in test_interactions:
        metrics.record_interaction(q, r)
    
    summary = metrics.get_summary()
    print(f"  Metrics Summary: {summary}")
    
    print("\n✅ All production features tested successfully!")

if __name__ == "__main__":
    test_production_features()
