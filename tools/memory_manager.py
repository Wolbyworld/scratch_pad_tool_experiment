#!/usr/bin/env python3
"""
Memory Manager for Luzia

Manages different memory systems (scratchpad, MCP) and provides unified interface.
"""

import os
from typing import Dict, Any, List, Optional
from .memory_interface import MemoryInterface
from .scratchpad_memory import ScratchpadMemory
from .mcp_memory import MCPMemory


class MemoryManager:
    """Manages memory systems and provides unified interface."""
    
    def __init__(self, memory_type: str = None):
        """
        Initialize memory manager with specified memory system.
        
        Args:
            memory_type: "scratchpad" or "mcp" (defaults to env var or "scratchpad")
        """
        self.memory_type = memory_type or os.getenv('MEMORY_SYSTEM', 'scratchpad')
        self.memory_system = self._initialize_memory_system(self.memory_type)
    
    def _initialize_memory_system(self, memory_type: str) -> MemoryInterface:
        """Initialize the selected memory system."""
        if memory_type.lower() == 'mcp':
            try:
                return MCPMemory()
            except Exception as e:
                print(f"⚠️  Failed to initialize MCP memory: {e}")
                print("🔄 Falling back to scratchpad memory...")
                return ScratchpadMemory()
        else:
            return ScratchpadMemory()
    
    def get_context(self, query: str) -> Dict[str, Any]:
        """Get context from the active memory system."""
        return self.memory_system.get_context(query)
    
    def store_information(self, query: str, response: str, context: Dict[str, Any] = None) -> bool:
        """Store information in the active memory system."""
        return self.memory_system.store_information(query, response, context)
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the active memory system."""
        return self.memory_system.search(query, limit)
    
    def get_system_info(self) -> Dict[str, str]:
        """Get information about the active memory system."""
        return {
            "type": self.memory_type,
            "name": self.memory_system.get_system_name(),
            "status": "active"
        }
    
    def switch_memory_system(self, new_type: str) -> bool:
        """Switch to a different memory system."""
        try:
            new_system = self._initialize_memory_system(new_type)
            self.memory_system = new_system
            self.memory_type = new_type
            return True
        except Exception as e:
            print(f"Failed to switch to {new_type} memory: {e}")
            return False


def select_memory_system() -> str:
    """Interactive memory system selection."""
    from colorama import Fore, Style
    
    print(f"{Fore.CYAN}🧠 Select Memory System:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}1. Scratchpad{Style.RESET_ALL} - File-based memory (current system)")
    print(f"{Fore.GREEN}2. MCP{Style.RESET_ALL} - Knowledge graph memory via Model Context Protocol")
    print()
    
    while True:
        try:
            choice = input(f"{Fore.YELLOW}Enter your choice (1-2): {Style.RESET_ALL}").strip()
            if choice == "1":
                return "scratchpad"
            elif choice == "2":
                return "mcp" 
            else:
                print(f"{Fore.RED}Invalid choice. Please enter 1 or 2.{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Defaulting to scratchpad memory.{Style.RESET_ALL}")
            return "scratchpad" 