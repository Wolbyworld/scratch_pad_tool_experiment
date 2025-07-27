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
    """MCP-based memory implementation using direct JSON file operations."""
    
    def __init__(self, mcp_config_path: str = "config/mcp_config.json"):
        """Initialize MCP memory with direct file access."""
        load_dotenv()
        
        # Initialize OpenAI client for text processing
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        
        # Set up MCP memory file path
        self.memory_file = "data/mcp_memory.json"
        self._ensure_memory_file()
    
    def _ensure_memory_file(self):
        """Ensure MCP memory file exists."""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.memory_file):
            # Create empty memory structure
            empty_memory = {
                "entities": [],
                "relations": []
            }
            with open(self.memory_file, 'w') as f:
                json.dump(empty_memory, f, indent=2)
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory data from JSON file."""
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"entities": [], "relations": []}
    
    def _save_memory(self, memory_data: Dict[str, Any]):
        """Save memory data to JSON file."""
        with open(self.memory_file, 'w') as f:
            json.dump(memory_data, f, indent=2)
    
    def get_context(self, query: str) -> Dict[str, Any]:
        """Get context by searching the knowledge graph."""
        try:
            memory_data = self._load_memory()
            
            # Search for relevant entities and observations
            relevant_info = []
            query_lower = query.lower()
            
            # Enhanced search logic for name-related queries
            is_name_query = any(keyword in query_lower for keyword in ['name', 'called', 'who am i', 'who are you'])
            
            # Search entities and their observations
            for entity in memory_data.get("entities", []):
                entity_name = entity.get("name", "").lower()
                entity_type = entity.get("entityType", "").lower()
                observations = entity.get("observations", [])
                
                # Enhanced matching logic
                name_match = query_lower in entity_name or entity_name in query_lower
                
                # For name queries, also check for name-related observations
                obs_match = False
                for obs in observations:
                    obs_lower = obs.lower()
                    # Direct substring match
                    if query_lower in obs_lower or obs_lower in query_lower:
                        obs_match = True
                        break
                    # Name-specific matching
                    if is_name_query and any(name_keyword in obs_lower for name_keyword in ['name', 'called']):
                        obs_match = True
                        break
                
                if name_match or obs_match:
                    info = f"{entity['name']} ({entity_type})"
                    if observations:
                        info += f": {', '.join(observations)}"
                    relevant_info.append(info)
            
            # Also check relations
            for relation in memory_data.get("relations", []):
                from_entity = relation.get("from", "").lower()
                to_entity = relation.get("to", "").lower()
                relation_type = relation.get("relationType", "").lower()
                
                if (query_lower in from_entity or from_entity in query_lower or
                    query_lower in to_entity or to_entity in query_lower):
                    relevant_info.append(f"{relation['from']} {relation['relationType']} {relation['to']}")
            
            if relevant_info:
                context_text = "From knowledge graph: " + "; ".join(relevant_info)
            else:
                context_text = "No relevant information found in knowledge graph."
            
            return {
                "status": "success",
                "relevant_context": context_text,
                "media_files_needed": False,
                "recommended_media": [],
                "reasoning": "Searched MCP knowledge graph file"
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
        """Store information by extracting entities and relations from conversation."""
        try:
            # Use OpenAI to extract structured information
            analysis_prompt = f"""
            Analyze this conversation and extract information to store in a knowledge graph:
            
            User Query: {query}
            AI Response: {response}
            
            Extract and return ONLY a JSON object with this structure:
            {{
                "entities": [
                    {{"name": "entity_name", "entityType": "person|concept|project|place|other", "observations": ["fact1", "fact2"]}}
                ],
                "relations": [
                    {{"from": "entity1", "to": "entity2", "relationType": "relationship_type"}}
                ]
            }}
            
            Focus on:
            - Names of people mentioned
            - User preferences or facts
            - Projects or activities
            - Relationships between entities
            
            Return only the JSON, no other text.
            """
            
            response_obj = self.client.responses.create(
                model="gpt-4.1",
                input=[{"role": "user", "content": analysis_prompt}],
                store=False,
                max_output_tokens=500,
                temperature=0.1
            )
            
            # Extract JSON from response
            response_text = self._extract_text_from_response(response_obj)
            
            # Try to parse JSON
            try:
                extracted_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group(1))
                else:
                    print(f"Could not parse JSON from: {response_text}")
                    return False
            
            # Load current memory and merge new data
            memory_data = self._load_memory()
            
            # Add new entities (avoiding duplicates)
            existing_entity_names = {entity["name"] for entity in memory_data.get("entities", [])}
            for entity in extracted_data.get("entities", []):
                if entity["name"] not in existing_entity_names:
                    memory_data.setdefault("entities", []).append(entity)
                else:
                    # Update existing entity with new observations
                    for existing_entity in memory_data["entities"]:
                        if existing_entity["name"] == entity["name"]:
                            for obs in entity.get("observations", []):
                                if obs not in existing_entity.get("observations", []):
                                    existing_entity.setdefault("observations", []).append(obs)
            
            # Add new relations (avoiding duplicates)
            existing_relations = set()
            for rel in memory_data.get("relations", []):
                existing_relations.add((rel["from"], rel["to"], rel["relationType"]))
            
            for relation in extracted_data.get("relations", []):
                rel_tuple = (relation["from"], relation["to"], relation["relationType"])
                if rel_tuple not in existing_relations:
                    memory_data.setdefault("relations", []).append(relation)
            
            # Save updated memory
            self._save_memory(memory_data)
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
    
    def _extract_text_from_response(self, response) -> str:
        """Extract text from OpenAI Responses API response."""
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
            return ""
        except Exception as e:
            return f"Error extracting response: {e}" 