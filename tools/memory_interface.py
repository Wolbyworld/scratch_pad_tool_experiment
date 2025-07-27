#!/usr/bin/env python3
"""
Memory Interface for Luzia

Abstract interface for different memory systems (scratchpad, MCP, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class MemoryInterface(ABC):
    """Abstract interface for memory systems."""
    
    @abstractmethod
    def get_context(self, query: str) -> Dict[str, Any]:
        """
        Get relevant context for a query.
        
        Args:
            query: The user's question or topic
            
        Returns:
            Dict with context information in standard format:
            {
                "status": "success|error",
                "relevant_context": "extracted relevant information",
                "media_files_needed": true/false,
                "recommended_media": ["list", "of", "file", "paths"],
                "reasoning": "explanation of context selection"
            }
        """
        pass
    
    @abstractmethod
    def store_information(self, query: str, response: str, context: Dict[str, Any] = None) -> bool:
        """
        Store new information from a conversation.
        
        Args:
            query: The user's query
            response: The AI's response
            context: Additional context from the conversation
            
        Returns:
            bool: True if storage was successful
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for specific information.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching items
        """
        pass
    
    @abstractmethod
    def get_system_name(self) -> str:
        """Return the name of this memory system."""
        pass 