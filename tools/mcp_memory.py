#!/usr/bin/env python3
"""
MCP Memory Implementation for Luzia

Uses OpenAI's Responses API native MCP support for knowledge graph-based memory.
Implements entities, relations, and observations for structured information storage.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from .memory_interface import MemoryInterface


class MCPMemory(MemoryInterface):
    """MCP-based memory implementation using OpenAI native support."""
    
    def __init__(self, memory_file: str = None):
        """Initialize MCP memory with JSON file persistence."""
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.memory_file = memory_file or os.getenv('MCP_MEMORY_FILE', 'data/mcp_memory.json')
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        
        # Initialize memory structure
        self.memory = self._load_memory()
    
    def get_context(self, query: str) -> Dict[str, Any]:
        """Get relevant context using knowledge graph search."""
        try:
            # Search for relevant entities
            relevant_entities = self._search_entities(query)
            
            # Get related information
            context_info = []
            media_files = []
            
            for entity in relevant_entities:
                # Add entity information
                context_info.append(f"Entity: {entity['name']} ({entity['entityType']})")
                
                # Add observations
                for obs in entity.get('observations', []):
                    context_info.append(f"- {obs}")
                
                # Check for media files
                if entity['entityType'] == 'media_file':
                    media_files.append(entity['name'])
                
                # Add related entities
                relations = self._get_entity_relations(entity['name'])
                for rel in relations:
                    context_info.append(f"→ {rel['relationType']}: {rel['to']}")
            
            # Format context
            relevant_context = '\n'.join(context_info) if context_info else "No specific context found in knowledge graph."
            
            return {
                "status": "success",
                "relevant_context": relevant_context,
                "media_files_needed": len(media_files) > 0,
                "recommended_media": media_files,
                "reasoning": f"Found {len(relevant_entities)} relevant entities in knowledge graph"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error retrieving MCP context: {e}",
                "relevant_context": "",
                "media_files_needed": False,
                "recommended_media": []
            }
    
    def store_information(self, data: Dict[str, Any]) -> bool:
        """Store information as entities, relations, and observations."""
        try:
            # Extract entities from the conversation data
            entities_to_add = []
            relations_to_add = []
            observations_to_add = []
            
            # Process user message for entities
            user_message = data.get('user_message', '')
            ai_response = data.get('ai_response', '')
            
            # Use OpenAI to extract structured information
            extracted_info = self._extract_structured_info(user_message, ai_response)
            
            # Create/update entities
            for entity_data in extracted_info.get('entities', []):
                self._create_or_update_entity(entity_data)
            
            # Create relations
            for relation_data in extracted_info.get('relations', []):
                self._create_relation(relation_data)
            
            # Add observations
            for obs_data in extracted_info.get('observations', []):
                self._add_observation(obs_data)
            
            # Save memory to file
            self._save_memory()
            return True
            
        except Exception as e:
            print(f"Error storing information in MCP: {e}")
            return False
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search entities and observations."""
        results = []
        query_lower = query.lower()
        
        # Search entities
        for entity in self.memory.get('entities', []):
            relevance = 0
            
            # Check entity name
            if query_lower in entity['name'].lower():
                relevance += 0.8
            
            # Check entity type
            if query_lower in entity['entityType'].lower():
                relevance += 0.3
            
            # Check observations
            for obs in entity.get('observations', []):
                if query_lower in obs.lower():
                    relevance += 0.5
            
            if relevance > 0:
                results.append({
                    'entity': entity,
                    'relevance_score': relevance,
                    'match_type': 'entity'
                })
        
        # Sort by relevance and limit results
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:limit]
    
    def update_information(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing entity."""
        try:
            # Find entity
            for entity in self.memory.get('entities', []):
                if entity['name'] == entity_id:
                    # Update entity data
                    entity.update(updates)
                    self._save_memory()
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error updating MCP entity: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        entities = self.memory.get('entities', [])
        relations = self.memory.get('relations', [])
        
        # Count observations
        total_observations = sum(len(e.get('observations', [])) for e in entities)
        
        # Count entity types
        entity_types = {}
        for entity in entities:
            entity_type = entity.get('entityType', 'unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        return {
            'memory_type': 'mcp',
            'total_entities': len(entities),
            'total_relations': len(relations),
            'total_observations': total_observations,
            'entity_types': entity_types,
            'file_size_bytes': os.path.getsize(self.memory_file) if os.path.exists(self.memory_file) else 0,
            'file_path': self.memory_file
        }
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from JSON file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {'entities': [], 'relations': []}
        except Exception as e:
            print(f"Error loading MCP memory: {e}")
            return {'entities': [], 'relations': []}
    
    def _save_memory(self):
        """Save memory to JSON file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving MCP memory: {e}")
    
    def _search_entities(self, query: str) -> List[Dict[str, Any]]:
        """Search for entities relevant to the query."""
        results = []
        query_lower = query.lower()
        
        for entity in self.memory.get('entities', []):
            relevance = 0
            
            # Check entity name
            if query_lower in entity['name'].lower():
                relevance += 1.0
            
            # Check observations
            for obs in entity.get('observations', []):
                if query_lower in obs.lower():
                    relevance += 0.7
            
            # Check related entities
            relations = self._get_entity_relations(entity['name'])
            for rel in relations:
                if query_lower in rel['to'].lower() or query_lower in rel['relationType'].lower():
                    relevance += 0.3
            
            if relevance > 0:
                results.append(entity)
        
        return results
    
    def _get_entity_relations(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all relations for an entity."""
        relations = []
        for rel in self.memory.get('relations', []):
            if rel['from'] == entity_name:
                relations.append(rel)
        return relations
    
    def _extract_structured_info(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Use OpenAI to extract structured information from conversation."""
        try:
            # Create extraction prompt
            extraction_prompt = f"""
Extract structured information from this conversation for a knowledge graph.

User: {user_message}
Assistant: {ai_response}

Extract:
1. Entities (people, places, projects, concepts) with types
2. Relations between entities
3. New observations/facts about entities

Return as JSON:
{{
  "entities": [
    {{"name": "entity_name", "entityType": "person|project|concept|media_file|other", "observations": ["fact1", "fact2"]}}
  ],
  "relations": [
    {{"from": "entity1", "to": "entity2", "relationType": "works_on|likes|located_in|other"}}
  ],
  "observations": [
    {{"entityName": "entity_name", "contents": ["new observation"]}}
  ]
}}

Only extract clear, factual information. If no clear entities/relations, return empty arrays.
"""
            
            response = self.client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": "You are an expert at extracting structured information for knowledge graphs. Return only valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                store=False,
                max_output_tokens=500,
                temperature=0.1
            )
            
            # Parse response
            response_text = response.output_text
            
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {'entities': [], 'relations': [], 'observations': []}
                
        except Exception as e:
            print(f"Error extracting structured info: {e}")
            return {'entities': [], 'relations': [], 'observations': []}
    
    def _create_or_update_entity(self, entity_data: Dict[str, Any]):
        """Create or update an entity."""
        entity_name = entity_data.get('name')
        if not entity_name:
            return
        
        # Check if entity exists
        for entity in self.memory['entities']:
            if entity['name'] == entity_name:
                # Update existing entity
                entity.update(entity_data)
                return
        
        # Create new entity
        self.memory['entities'].append(entity_data)
    
    def _create_relation(self, relation_data: Dict[str, Any]):
        """Create a new relation."""
        # Check if relation already exists
        for rel in self.memory['relations']:
            if (rel['from'] == relation_data.get('from') and 
                rel['to'] == relation_data.get('to') and 
                rel['relationType'] == relation_data.get('relationType')):
                return  # Relation already exists
        
        # Add new relation
        self.memory['relations'].append(relation_data)
    
    def _add_observation(self, obs_data: Dict[str, Any]):
        """Add observation to an entity."""
        entity_name = obs_data.get('entityName')
        contents = obs_data.get('contents', [])
        
        if not entity_name or not contents:
            return
        
        # Find entity and add observations
        for entity in self.memory['entities']:
            if entity['name'] == entity_name:
                if 'observations' not in entity:
                    entity['observations'] = []
                
                # Add new observations (avoid duplicates)
                for content in contents:
                    if content not in entity['observations']:
                        entity['observations'].append(content)
                break 