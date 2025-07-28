#!/usr/bin/env python3
"""
MCP Memory Implementation

Uses the actual MCP (Model Context Protocol) server via JSON-RPC communication.
"""

import os
import json
import subprocess
import threading
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from .memory_interface import MemoryInterface


class MCPMemory(MemoryInterface):
    """Real MCP implementation using JSON-RPC communication with MCP server."""
    
    def __init__(self, mcp_config_path: str = "config/mcp_config.json"):
        """Initialize MCP memory with actual MCP server."""
        load_dotenv()
        
        # Initialize OpenAI client for text processing
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        
        # Start MCP server
        self.mcp_process = None
        self._start_mcp_server()
    
    def _start_mcp_server(self):
        """Start the actual MCP memory server."""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Set environment variable for memory file (absolute path)
            env = os.environ.copy()
            memory_file_path = os.path.abspath('./data/mcp_memory.json')
            env['MEMORY_FILE_PATH'] = memory_file_path
            
            # Ensure the memory file exists
            if not os.path.exists(memory_file_path):
                with open(memory_file_path, 'w') as f:
                    json.dump({"entities": [], "relations": []}, f, indent=2)
            
            # Start MCP server process
            self.mcp_process = subprocess.Popen(
                ['npx', '-y', '@modelcontextprotocol/server-memory'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=0  # Unbuffered
            )
            
            # Initialize the server
            self._initialize_mcp_server()
            
            print("🚀 MCP Server started successfully")
            
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            raise
    
    def _initialize_mcp_server(self):
        """Initialize MCP server with proper handshake."""
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "resources": {},
                    "tools": {}
                },
                "clientInfo": {
                    "name": "luzia",
                    "version": "1.0.0"
                }
            }
        }
        
        self._send_request(init_request)
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        self._send_request(initialized_notification)
        
        # Query available tools (verify connection)
        tools_request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/list"
        }
        
        tools_response = self._send_request(tools_request)
        if "result" in tools_response:
            print(f"✅ MCP tools loaded: {len(tools_response['result']['tools'])} available")
    
    def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server."""
        try:
            request_json = json.dumps(request) + '\n'
            self.mcp_process.stdin.write(request_json)
            self.mcp_process.stdin.flush()
            
            # Read response if expecting one (has 'id')
            if 'id' in request:
                response_line = self.mcp_process.stdout.readline()
                if response_line:
                    return json.loads(response_line.strip())
            
            return {}
            
        except Exception as e:
            print(f"❌ MCP communication error: {e}")
            return {"error": str(e)}
    
    def __del__(self):
        """Clean up MCP server process."""
        if self.mcp_process:
            self.mcp_process.terminate()
            self.mcp_process.wait()
    
    def get_context(self, query: str) -> Dict[str, Any]:
        """Get context using MCP search_nodes tool."""
        try:
            # Use MCP search_nodes tool
            search_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_nodes",
                    "arguments": {
                        "query": query
                    }
                }
            }
            
            response = self._send_request(search_request)
            
            if "result" in response:
                search_results = response["result"].get("content", [])
                
                # Format the results
                if search_results:
                    context_parts = []
                    for result in search_results:
                        if isinstance(result, dict) and "text" in result:
                            context_parts.append(result["text"])
                        elif isinstance(result, str):
                            context_parts.append(result)
                    
                    context_text = "From MCP knowledge graph: " + "; ".join(context_parts)
                else:
                    context_text = "No relevant information found in MCP knowledge graph."
                
                return {
                    "status": "success",
                    "relevant_context": context_text,
                    "media_files_needed": False,
                    "recommended_media": [],
                    "reasoning": "Searched using MCP search_nodes tool"
                }
            else:
                error_msg = response.get("error", {}).get("message", "Unknown MCP error")
                return {
                    "status": "error", 
                    "message": f"MCP search error: {error_msg}",
                    "relevant_context": "",
                    "media_files_needed": False,
                    "recommended_media": []
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error communicating with MCP server: {e}",
                "relevant_context": "",
                "media_files_needed": False,
                "recommended_media": []
            }
    
    def store_information(self, query: str, response: str, context: Dict[str, Any] = None) -> bool:
        """Store information using MCP create_entities, create_relations, and add_observations tools."""
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
            
            # Use MCP tools to store the data
            success = True
            
            # 1. Create entities
            entities = extracted_data.get("entities", [])
            if entities:
                create_entities_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "create_entities",
                        "arguments": {
                            "entities": entities
                        }
                    }
                }
                
                result = self._send_request(create_entities_request)
                if "error" in result:
                    print(f"MCP create_entities error: {result['error']}")
                    success = False
            
            # 2. Create relations
            relations = extracted_data.get("relations", [])
            if relations:
                create_relations_request = {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "create_relations",
                        "arguments": {
                            "relations": relations
                        }
                    }
                }
                
                result = self._send_request(create_relations_request)
                if "error" in result:
                    print(f"MCP create_relations error: {result['error']}")
                    success = False
            
            return success
            
        except Exception as e:
            print(f"Error storing information in MCP: {e}")
            return False
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search MCP knowledge graph using search_nodes tool."""
        try:
            search_request = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "search_nodes",
                    "arguments": {
                        "query": query
                    }
                }
            }
            
            response = self._send_request(search_request)
            
            if "result" in response:
                search_results = response["result"].get("content", [])
                
                # Format the results
                formatted_results = []
                for result in search_results[:limit]:
                    if isinstance(result, dict) and "text" in result:
                        formatted_results.append({
                            "content": result["text"],
                            "source": "MCP",
                            "relevance": 1.0
                        })
                    elif isinstance(result, str):
                        formatted_results.append({
                            "content": result,
                            "source": "MCP", 
                            "relevance": 1.0
                        })
                
                return formatted_results
            else:
                print(f"MCP search error: {response.get('error', {})}")
                return []
            
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