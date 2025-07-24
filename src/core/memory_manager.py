#!/usr/bin/env python3
"""
Memory Manager Module

Handles conversation memory and context caching:
- ChatMemoryBuffer management
- Context caching for current topics
- Memory persistence and cleanup
"""

from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from typing import Optional, List, Dict, Any

from .models import ReasoningTriplet


class MemoryManager:
    """Manages conversation memory and context caching"""
    
    def __init__(self, token_limit: int = 3000):
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=token_limit)
        
        # Context caching for current topic
        self.current_topic_triplet: Optional[ReasoningTriplet] = None
        self.current_topic_source_nodes: Optional[List] = None
        self.stuck_count: int = 0
        
        # Session metadata
        self.session_metadata: Dict[str, Any] = {
            "total_interactions": 0,
            "topics_covered": [],
            "scaffolding_instances": 0
        }
    
    def add_user_message(self, message: str) -> None:
        """
        Add user message to conversation memory
        
        Args:
            message: User's message content
        """
        try:
            chat_message = ChatMessage(role=MessageRole.USER, content=message)
            self.memory.put(chat_message)
            self.session_metadata["total_interactions"] += 1
            
        except Exception as e:
            print(f"Error adding user message to memory: {e}")
    
    def add_assistant_message(self, message: str) -> None:
        """
        Add assistant message to conversation memory
        
        Args:
            message: Assistant's response content
        """
        try:
            chat_message = ChatMessage(role=MessageRole.ASSISTANT, content=message)
            self.memory.put(chat_message)
            
        except Exception as e:
            print(f"Error adding assistant message to memory: {e}")
    
    def get_conversation_history(self, last_n: int = None) -> List[ChatMessage]:
        """
        Get conversation history
        
        Args:
            last_n: Number of recent messages to retrieve (None for all)
            
        Returns:
            List[ChatMessage]: Recent conversation messages
        """
        try:
            all_messages = self.memory.get_all()
            if last_n is None:
                return all_messages
            return all_messages[-last_n:] if all_messages else []
            
        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []
    
    def format_conversation_context(self, last_n: int = 6) -> str:
        """
        Format recent conversation for use in prompts
        
        Args:
            last_n: Number of recent messages to include
            
        Returns:
            str: Formatted conversation context
        """
        try:
            recent_messages = self.get_conversation_history(last_n)
            
            if not recent_messages:
                return "This is the start of our conversation."
            
            # Format messages
            formatted_parts = []
            for msg in recent_messages:
                role = "Student" if msg.role == MessageRole.USER else "Tutor"
                # Truncate long messages for context
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                formatted_parts.append(f"{role}: {content}")
            
            return "\n".join(formatted_parts)
            
        except Exception as e:
            print(f"Error formatting conversation context: {e}")
            return "Conversation context unavailable."
    
    def cache_topic_context(self, triplet: ReasoningTriplet, source_nodes: List) -> None:
        """
        Cache the current topic's context for fast follow-up processing
        
        Args:
            triplet: Expert reasoning triplet
            source_nodes: Retrieved source nodes
        """
        try:
            self.current_topic_triplet = triplet
            self.current_topic_source_nodes = source_nodes
            
            # Add to topics covered
            if triplet and triplet.question:
                topic_summary = triplet.question[:50] + "..." if len(triplet.question) > 50 else triplet.question
                if topic_summary not in self.session_metadata["topics_covered"]:
                    self.session_metadata["topics_covered"].append(topic_summary)
                    
        except Exception as e:
            print(f"Error caching topic context: {e}")
    
    def get_cached_context(self) -> tuple:
        """
        Get cached topic context
        
        Returns:
            tuple: (ReasoningTriplet, source_nodes)
        """
        return self.current_topic_triplet, self.current_topic_source_nodes
    
    def has_cached_context(self) -> bool:
        """
        Check if there's cached context available
        
        Returns:
            bool: True if context is cached
        """
        return self.current_topic_triplet is not None
    
    def clear_topic_cache(self) -> None:
        """Clear cached topic context"""
        self.current_topic_triplet = None
        self.current_topic_source_nodes = None
        self.stuck_count = 0
    
    def increment_stuck_count(self) -> int:
        """
        Increment stuck count for scaffolding
        
        Returns:
            int: New stuck count
        """
        self.stuck_count += 1
        self.session_metadata["scaffolding_instances"] += 1
        return self.stuck_count
    
    def reset_stuck_count(self) -> None:
        """Reset stuck count when student provides answer"""
        self.stuck_count = 0
    
    def get_stuck_count(self) -> int:
        """Get current stuck count"""
        return self.stuck_count
    
    def clear_conversation_memory(self) -> None:
        """Clear conversation memory"""
        try:
            self.memory.reset()
            
        except Exception as e:
            print(f"Error clearing conversation memory: {e}")
    
    def reset_session(self) -> None:
        """Reset entire session - memory, cache, and metadata"""
        try:
            # Clear memory
            self.clear_conversation_memory()
            
            # Clear topic cache
            self.clear_topic_cache()
            
            # Reset metadata
            self.session_metadata = {
                "total_interactions": 0,
                "topics_covered": [],
                "scaffolding_instances": 0
            }
            
        except Exception as e:
            print(f"Error resetting session: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session
        
        Returns:
            Dict: Session summary with statistics
        """
        try:
            conversation_length = len(self.get_conversation_history())
            
            summary = {
                **self.session_metadata,
                "conversation_length": conversation_length,
                "has_cached_context": self.has_cached_context(),
                "current_stuck_count": self.stuck_count
            }
            
            return summary
            
        except Exception as e:
            print(f"Error generating session summary: {e}")
            return {"error": "Unable to generate session summary"}
    
    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """
        Get memory usage statistics
        
        Returns:
            Dict: Memory usage stats
        """
        try:
            all_messages = self.get_conversation_history()
            
            total_chars = sum(len(msg.content) for msg in all_messages)
            user_messages = [msg for msg in all_messages if msg.role == MessageRole.USER]
            assistant_messages = [msg for msg in all_messages if msg.role == MessageRole.ASSISTANT]
            
            return {
                "total_messages": len(all_messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "total_characters": total_chars,
                "average_message_length": total_chars // len(all_messages) if all_messages else 0
            }
            
        except Exception as e:
            print(f"Error calculating memory usage stats: {e}")
            return {"error": "Unable to calculate memory stats"}
