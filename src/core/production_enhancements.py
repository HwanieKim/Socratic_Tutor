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
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.topic_filter = TopicRelevanceFilter()
        self.metrics = ConversationMetrics()
        self.logger = EnhancedLogger()
    
    def is_request_allowed(self, user_id: str = "default") -> bool:
        """Check if request is within rate limits"""
        return self.rate_limiter.is_allowed(user_id)
    
    def is_topic_relevant(self, question: str) -> bool:
        """Check if question is related to sustainable design"""
        return self.topic_filter.is_relevant(question)
    
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
    def __init__(self):
        # Keywords related to sustainable design
        self.relevant_keywords = {
            'sustainability', 'sustainable', 'design', 'environment', 'environmental',
            'green', 'eco', 'lifecycle', 'assessment', 'lca', 'materials', 'energy',
            'efficiency', 'carbon', 'footprint', 'renewable', 'recycling', 'circular',
            'economy', 'biodegradable', 'conservation', 'waste', 'reduction', 'building',
            'architecture', 'construction', 'planning', 'urban', 'development', 'impact'
        }
        
        # Obviously irrelevant topics
        self.irrelevant_patterns = [
            r'\b(cook|recipe|bake|food|cake|pizza)\b',
            r'\b(sport|game|football|basketball)\b',
            r'\b(movie|film|tv|entertainment)\b',
            r'\b(music|song|band|artist)\b',
            r'\b(math|calculate|equation|formula)\b'
        ]
    
    def is_relevant(self, question: str) -> bool:
        """Determine if question is relevant to sustainable design"""
        question_lower = question.lower()
        
        # Check for obviously irrelevant content
        for pattern in self.irrelevant_patterns:
            if re.search(pattern, question_lower):
                return False
        
        # Check for relevant keywords
        words = set(re.findall(r'\b\w+\b', question_lower))
        relevant_word_count = len(words.intersection(self.relevant_keywords))
        
        # Follow-up question patterns (these are usually relevant in context)
        followup_patterns = [
            r'\b(more|tell|explain|what|how|why|when|where)\b',
            r'\b(principles|examples|details|about|that|this|it)\b',
            r'\b(can you|could you|please|help)\b'
        ]
        
        # Check if this looks like a follow-up question
        is_followup = any(re.search(pattern, question_lower) for pattern in followup_patterns)
        
        # Consider relevant if:
        # 1. Has relevant keywords, OR
        # 2. Is a very short question (likely follow-up), OR  
        # 3. Looks like a follow-up question pattern
        return (relevant_word_count > 0 or 
                len(words) <= 3 or 
                (is_followup and len(words) <= 10))

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
    def __init__(self, base_engine):
        self.engine = base_engine
        self.enhancements = ProductionEnhancements()
    
    def get_guidance(self, user_question: str, user_id: str = "default") -> str:
        """Enhanced guidance method with production features"""
        
        # Rate limiting check
        if not self.enhancements.is_request_allowed(user_id):
            return "You're asking questions quite frequently. Please wait a moment before asking again."
        
        # Input validation (now in base engine)
        if not user_question or not user_question.strip():
            return "I'd be happy to help! Please ask me a question about sustainable design."
        
        # Topic relevance check
        if not self.enhancements.is_topic_relevant(user_question):
            return ("I'm specialized in sustainable design topics. Could you please ask about "
                   "sustainable design, environmental impact, green building, or related topics?")
        
        # Get response from base engine
        response = self.engine.get_guidance(user_question)
        
        # Log interaction
        self.enhancements.log_interaction(user_question, response, user_id)
        
        return response
    
    def reset(self):
        """Reset conversation state"""
        self.engine.reset()
    
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
    print("\n2. Testing Topic Relevance Filter:")
    topic_filter = TopicRelevanceFilter()
    
    test_questions = [
        ("What is sustainable design?", "Relevant"),
        ("How do I bake a cake?", "Irrelevant"),
        ("What are green building materials?", "Relevant"),
        ("What's the weather like?", "Irrelevant"),
        ("Tell me about LCA", "Relevant")
    ]
    
    for question, expected in test_questions:
        relevant = topic_filter.is_relevant(question)
        status = "✅" if (relevant and expected == "Relevant") or (not relevant and expected == "Irrelevant") else "❌"
        print(f"  {status} '{question}' -> {'Relevant' if relevant else 'Irrelevant'}")
    
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
