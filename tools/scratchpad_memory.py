#!/usr/bin/env python3
"""
Scratchpad Memory Adapter

Adapter for the existing file-based scratchpad system to work with the MemoryInterface.
"""

from typing import Dict, Any, List
from .memory_interface import MemoryInterface
from .scratchpad_tools import ScratchPadTools
from update_manager import apply_conversation_updates


class ScratchpadMemory(MemoryInterface):
    """Adapter for existing scratchpad system implementing MemoryInterface."""
    
    def __init__(self, scratchpad_file: str = None, system_prompt_file: str = None):
        """Initialize scratchpad memory with existing tools."""
        self.scratchpad_tools = ScratchPadTools(scratchpad_file, system_prompt_file)
    
    def get_context(self, query: str) -> Dict[str, Any]:
        """Get context using existing scratchpad tools."""
        return self.scratchpad_tools.get_scratch_pad_context(query)
    
    def store_information(self, query: str, response: str, context: Dict[str, Any] = None) -> bool:
        """Store information using existing update manager."""
        try:
            # Use existing update manager
            apply_conversation_updates(
                user_message=query,
                ai_response=response,
                function_calls=context.get("tools_called", []) if context else [],
                tool_responses=context.get("tool_responses", []) if context else []
            )
            return True
            
        except Exception as e:
            print(f"Error storing information in scratchpad: {e}")
            return False
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Simple search by getting context (scratchpad doesn't have dedicated search)."""
        try:
            context_result = self.get_context(query)
            if context_result.get("status") == "success":
                return [{
                    "content": context_result.get("relevant_context", ""),
                    "source": "scratchpad",
                    "relevance": 1.0
                }]
            return []
        except Exception:
            return []
    
    def get_system_name(self) -> str:
        """Return system name."""
        return "scratchpad" 