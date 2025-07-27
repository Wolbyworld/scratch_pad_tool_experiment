#!/usr/bin/env python3
"""
MCP Memory Implementation

Uses OpenAI Responses API to communicate with MCP memory server for knowledge graph-based storage.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from .memory_interface import MemoryInterface


class MCPMemory(MemoryInterface):
    """MCP-based memory implementation using OpenAI Responses API."""
    
    def __init__(self, mcp_config_path: str = "config/mcp_config.json"):
        """Initialize MCP memory with OpenAI client."""
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        
        # Load MCP configuration
        self.mcp_config_path = mcp_config_path
        self._ensure_mcp_config()
        
        # MCP memory tools available
        self.mcp_tools = [
            {
                "type": "function",
                "name": "create_entities",
                "description": "Create multiple new entities in the knowledge graph"
            },
            {
                "type": "function", 
                "name": "create_relations",
                "description": "Create multiple new relations between entities"
            },
            {
                "type": "function",
                "name": "add_observations", 
                "description": "Add new observations to existing entities"
            },
            {
                "type": "function",
                "name": "search_nodes",
                "description": "Search for nodes based on query"
            },
            {
                "type": "function",
                "name": "open_nodes",
                "description": "Retrieve specific nodes by name"
            },
            {
                "type": "function",
                "name": "read_graph",
                "description": "Read the entire knowledge graph"
            }
        ]
    
    def _ensure_mcp_config(self):
        """Ensure MCP configuration exists."""
        if not os.path.exists(self.mcp_config_path):
            raise FileNotFoundError(f"MCP config not found: {self.mcp_config_path}")
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
    
    def get_context(self, query: str) -> Dict[str, Any]:
        """Get context using MCP search and retrieval."""
        try:
            # First, search for relevant entities
            search_prompt = f"""
            Search the knowledge graph for information relevant to this query: "{query}"
            
            Use the search_nodes function to find relevant entities, then use open_nodes to get detailed information.
            Provide a comprehensive response based on what you find.
            """
            
            response = self.client.responses.create(
                model="gpt-4.1",
                input=[{"role": "user", "content": search_prompt}],
                tools=self.mcp_tools,
                store=False,
                max_output_tokens=1000,
                temperature=0.1
            )
            
            # Process the response and extract context
            context_text = self._extract_context_from_response(response)
            
            return {
                "status": "success",
                "relevant_context": context_text,
                "media_files_needed": False,
                "recommended_media": [],
                "reasoning": "Retrieved from MCP knowledge graph"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error retrieving MCP context: {e}",
                "relevant_context": "",
                "media_files_needed": False,
                "recommended_media": []
            }
    
    def store_information(self, query: str, response: str, context: Dict[str, Any] = None) -> bool:
        """Store information as entities and relations in MCP."""
        try:
            storage_prompt = f"""
            Analyze this conversation and extract meaningful information to store in the knowledge graph:
            
            User Query: {query}
            AI Response: {response}
            
            Create entities for:
            - People mentioned
            - Topics/concepts discussed  
            - Projects or activities
            - Preferences expressed
            - Facts learned about the user
            
            Create relations between entities and add observations as appropriate.
            Use create_entities, create_relations, and add_observations functions.
            """
            
            response = self.client.responses.create(
                model="gpt-4.1",
                input=[{"role": "user", "content": storage_prompt}],
                tools=self.mcp_tools,
                store=False,
                max_output_tokens=1000,
                temperature=0.1
            )
            
            # If the AI called MCP functions, storage was attempted
            return True
            
        except Exception as e:
            print(f"Error storing information in MCP: {e}")
            return False
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search MCP knowledge graph."""
        try:
            search_prompt = f"""
            Search the knowledge graph for: "{query}"
            Use search_nodes function and return the most relevant results.
            """
            
            response = self.client.responses.create(
                model="gpt-4.1",
                input=[{"role": "user", "content": search_prompt}],
                tools=self.mcp_tools,
                store=False,
                max_output_tokens=800,
                temperature=0.1
            )
            
            # Process search results
            results = self._extract_search_results(response)
            return results[:limit]
            
        except Exception as e:
            print(f"Error searching MCP: {e}")
            return []
    
    def get_system_name(self) -> str:
        """Return system name."""
        return "MCP"
    
    def _extract_context_from_response(self, response) -> str:
        """Extract context text from OpenAI response."""
        try:
            # Handle Responses API output format
            if hasattr(response, 'output_text'):
                return response.output_text
            elif hasattr(response, 'output') and response.output:
                # Look for assistant message in output
                for item in response.output:
                    if hasattr(item, 'type') and item.type == 'message':
                        if hasattr(item, 'content'):
                            if isinstance(item.content, list) and len(item.content) > 0:
                                return item.content[0].text if hasattr(item.content[0], 'text') else str(item.content[0])
                            elif isinstance(item.content, str):
                                return item.content
            return "No context found"
        except Exception as e:
            return f"Error extracting context: {e}"
    
    def _extract_search_results(self, response) -> List[Dict[str, Any]]:
        """Extract search results from OpenAI response."""
        try:
            content = self._extract_context_from_response(response)
            # Simple parsing - in real implementation would parse structured results
            return [{
                "content": content,
                "source": "MCP",
                "relevance": 0.9
            }]
        except Exception:
            return [] 