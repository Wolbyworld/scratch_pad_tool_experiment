#!/usr/bin/env python3
"""
Memory Interface for Luzia

Abstract interface that both scratchpad and MCP memory systems implement.
Provides a unified API for context retrieval and information storage.
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
            Dict containing relevant context, media recommendations, etc.
        """
        pass
    
    @abstractmethod
    def store_information(self, data: Dict[str, Any]) -> bool:
        """
        Store new information in the memory system.
        
        Args:
            data: Information to store (conversation context, user facts, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for specific information in the memory system.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching entries
        """
        pass
    
    @abstractmethod
    def update_information(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update existing information in the memory system.
        
        Args:
            entity_id: Identifier for the information to update
            updates: New information to apply
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system.
        
        Returns:
            Dict with stats like entity count, storage size, etc.
        """
        pass 