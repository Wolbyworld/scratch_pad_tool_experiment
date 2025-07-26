#!/usr/bin/env python3
"""
Scratch Pad Tools for Luzia

Focused on extracting relevant context from the user's scratch pad document.
Single responsibility: context extraction and analysis only.
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI


class ScratchPadTools:
    """Focused scratch pad context extraction functionality."""
    
    def __init__(self, scratchpad_file: str = None, system_prompt_file: str = None):
        """Initialize the scratch pad tools.
        
        Args:
            scratchpad_file: Path to scratch pad file
            system_prompt_file: Path to system prompt file
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        
        # Set file paths
        self.scratchpad_file = scratchpad_file or os.getenv('SCRATCHPAD_FILE', 'scratchpad.txt')
        self.system_prompt_file = system_prompt_file or os.getenv('SYSTEM_PROMPT_FILE', 'config/system_prompt.txt')
    
    def _load_scratchpad(self) -> str:
        """Load the scratch pad content from file."""
        try:
            with open(self.scratchpad_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            return f"Error: Scratch pad file not found: {self.scratchpad_file}"
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt content from file."""
        try:
            with open(self.system_prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "You are a context extraction specialist. Return valid JSON only."
    
    def get_scratch_pad_context(self, query: str) -> Dict[str, Any]:
        """
        Get relevant context from the scratch pad for a given query.
        This function is marked as REQUIRED and will always be called by GPT-4.1.
        
        Args:
            query: The user's question or topic
            
        Returns:
            Dict containing relevant context and media recommendations
        """
        try:
            # Load scratch pad content
            scratchpad_content = self._load_scratchpad()
            
            if scratchpad_content.startswith("Error:"):
                return {
                    "status": "error",
                    "message": scratchpad_content,
                    "relevant_context": "",
                    "media_files_needed": False,
                    "recommended_media": []
                }
            
            # Load the system prompt with sophisticated media assessment rules
            system_prompt = self._load_system_prompt()
            
            # Create user message with query and scratch pad content
            user_message = f"""USER QUERY: {query}

SCRATCH PAD CONTENT:
{scratchpad_content}

Please follow the system prompt rules to determine if media files are needed and provide your response in JSON format:
{{
    "relevant_context": "extracted relevant information",
    "media_files_needed": true/false,
    "recommended_media": ["list", "of", "file", "paths"],
    "reasoning": "why these media files would be helpful (or why not needed)"
}}"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            # Parse the response
            response_content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            try:
                # Find JSON in the response (might be wrapped in markdown)
                start_idx = response_content.find('{')
                end_idx = response_content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_content[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    # Fallback if no JSON found
                    analysis = {
                        "relevant_context": response_content,
                        "media_files_needed": False,
                        "recommended_media": [],
                        "reasoning": "JSON parsing failed, using raw response"
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = {
                    "relevant_context": response_content,
                    "media_files_needed": False,
                    "recommended_media": [],
                    "reasoning": "JSON parsing failed, using raw response"
                }
            
            return {
                "status": "success",
                "query": query,
                "relevant_context": analysis.get("relevant_context", ""),
                "media_files_needed": analysis.get("media_files_needed", False),
                "recommended_media": analysis.get("recommended_media", []),
                "reasoning": analysis.get("reasoning", "")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing scratch pad context: {e}",
                "relevant_context": "",
                "media_files_needed": False,
                "recommended_media": []
            } 