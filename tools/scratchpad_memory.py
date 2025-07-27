#!/usr/bin/env python3
"""
Scratchpad Memory Adapter for Luzia

Adapter that wraps the existing scratchpad system to implement the MemoryInterface.
Provides backward compatibility while enabling the new memory system architecture.
"""

import os
import re
from typing import Dict, Any, List
from .memory_interface import MemoryInterface
from .scratchpad_tools import ScratchPadTools
from update_manager import apply_conversation_updates


class ScratchpadMemory(MemoryInterface):
    """Adapter for existing scratchpad system."""
    
    def __init__(self, scratchpad_file: str = None, system_prompt_file: str = None):
        """Initialize the scratchpad memory adapter."""
        self.scratchpad_tools = ScratchPadTools(scratchpad_file, system_prompt_file)
        self.scratchpad_file = scratchpad_file or os.getenv('SCRATCHPAD_FILE', 'scratchpad.txt')
    
    def get_context(self, query: str) -> Dict[str, Any]:
        """Get relevant context using existing scratchpad tools."""
        return self.scratchpad_tools.get_scratch_pad_context(query)
    
    def store_information(self, data: Dict[str, Any]) -> bool:
        """Store information using existing update manager."""
        try:
            # Convert data to the format expected by update_manager
            conversation_data = {
                'user_message': data.get('user_message', ''),
                'ai_response': data.get('ai_response', ''),
                'function_calls': data.get('function_calls', []),
                'scratchpad_content': data.get('scratchpad_content', '')
            }
            
            # Use existing update system
            apply_conversation_updates(conversation_data)
            return True
            
        except Exception as e:
            print(f"Error storing information in scratchpad: {e}")
            return False
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Simple text search in scratchpad content."""
        try:
            # Load scratchpad content
            content = self._load_scratchpad_content()
            
            # Simple keyword search
            results = []
            lines = content.split('\n')
            query_lower = query.lower()
            
            for i, line in enumerate(lines):
                if query_lower in line.lower() and line.strip():
                    results.append({
                        'line_number': i + 1,
                        'content': line.strip(),
                        'relevance_score': self._calculate_relevance(line, query)
                    })
                    
                    if len(results) >= limit:
                        break
            
            # Sort by relevance
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results
            
        except Exception as e:
            print(f"Error searching scratchpad: {e}")
            return []
    
    def update_information(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update information in scratchpad (limited functionality)."""
        # For now, treat updates as new information to store
        return self.store_information(updates)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the scratchpad."""
        try:
            content = self._load_scratchpad_content()
            lines = content.split('\n')
            
            # Count different sections
            user_facts = len([l for l in lines if l.strip() and 'USER FACTS' in content])
            media_files = len([l for l in lines if l.strip() and 'MEDIA DOCUMENTS' in content])
            
            return {
                'memory_type': 'scratchpad',
                'total_lines': len(lines),
                'non_empty_lines': len([l for l in lines if l.strip()]),
                'estimated_user_facts': user_facts,
                'estimated_media_files': media_files,
                'file_size_bytes': len(content.encode('utf-8')),
                'file_path': self.scratchpad_file
            }
            
        except Exception as e:
            return {
                'memory_type': 'scratchpad',
                'error': str(e)
            }
    
    def _load_scratchpad_content(self) -> str:
        """Load the scratchpad content from file."""
        try:
            with open(self.scratchpad_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""
    
    def _calculate_relevance(self, line: str, query: str) -> float:
        """Calculate relevance score for a line based on query."""
        line_lower = line.lower()
        query_lower = query.lower()
        
        # Exact match gets highest score
        if query_lower in line_lower:
            return 1.0
        
        # Word overlap scoring
        query_words = set(query_lower.split())
        line_words = set(line_lower.split())
        overlap = len(query_words.intersection(line_words))
        
        if len(query_words) > 0:
            return overlap / len(query_words)
        
        return 0.0 