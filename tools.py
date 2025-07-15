#!/usr/bin/env python3
"""
Function Calling Tools for Luzia

Contains functions that GPT-4.1 can call to enrich conversation context
with scratch pad information and media analysis.
"""

import os
import json
import base64
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
import fitz  # PyMuPDF for PDF processing


class ScratchPadTools:
    """Function calling tools for Luzia's context enrichment."""
    
    def __init__(self, scratchpad_file: str = None, system_prompt_file: str = None):
        """Initialize the tools.
        
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
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for OpenAI API."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            return f"Error encoding image: {e}"

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

    def analyze_media_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a media file (image) and return detailed description.
        This function is called when the scratch pad indicates media analysis is needed.
        
        Args:
            file_path: Path to the media file to analyze
            
        Returns:
            Dict containing media analysis results
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "message": f"Media file not found: {file_path}",
                    "analysis": "",
                    "file_type": "unknown"
                }
            
            # Get file extension to determine type
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                # Handle image files
                return self._analyze_image(file_path)
            elif file_ext == '.pdf':
                # Handle PDF files
                return self._analyze_pdf(file_path)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported file type: {file_ext}",
                    "analysis": "",
                    "file_type": file_ext
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing media file: {e}",
                "analysis": "",
                "file_type": "unknown"
            }
    
    def _analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze a PDF file by extracting text and providing intelligent summary."""
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            # Extract text from all pages
            text_content = ""
            pages = len(doc)
            for page_num in range(pages):
                page = doc[page_num]
                text_content += f"\n--- Page {page_num + 1} ---\n"
                text_content += page.get_text()
            
            doc.close()
            
            # Get basic document info
            words = len(text_content.split())
            chars = len(text_content)
            
            # Use GPT to analyze the PDF content
            analysis_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a document analysis specialist. Analyze the provided PDF text content and provide:
1. A comprehensive summary of the document
2. Key topics and themes
3. Important information that would be relevant for personal knowledge management
4. Document type and purpose
5. Any actionable insights or important details

Be thorough but concise."""
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this PDF document content:

DOCUMENT CONTENT:
{text_content[:12000]}  # Limit to avoid token limits

DOCUMENT STATISTICS:
- Pages: {pages}
- Words: {words}
- Characters: {chars}

Please provide a detailed analysis of this document."""
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            analysis = analysis_response.choices[0].message.content
            
            return {
                "status": "success",
                "file_path": pdf_path,
                "file_type": "pdf",
                "analysis": analysis,
                "extracted_text": text_content[:2000],  # First 2000 chars for reference
                "document_stats": {
                    "pages": pages,
                    "words": words,
                    "characters": chars
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing PDF: {e}",
                "analysis": "",
                "file_type": "pdf"
            }
    
    def _analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze an image file using GPT-4o-mini vision capabilities."""
        try:
            # Encode image to base64
            base64_image = self._encode_image(image_path)
            
            if base64_image.startswith("Error"):
                return {
                    "status": "error",
                    "message": base64_image,
                    "analysis": "",
                    "file_type": "image"
                }
            
            # Get file extension for proper MIME type
            file_ext = os.path.splitext(image_path)[1].lower()
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(file_ext, 'image/png')
            
            # Analyze image with GPT-4o-mini
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image in detail. Describe what you see, including objects, people, text, colors, composition, and any other relevant details that would be helpful for someone asking about this image."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "status": "success",
                "file_path": image_path,
                "file_type": "image",
                "analysis": analysis,
                "mime_type": mime_type
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing image: {e}",
                "analysis": "",
                "file_type": "image"
            }

    def analyze_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a PDF file and return detailed text analysis.
        This function is specifically for PDF document analysis.
        
        Args:
            file_path: Path to the PDF file to analyze
            
        Returns:
            Dict containing PDF analysis results with extracted text and AI analysis
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "message": f"PDF file not found: {file_path}",
                    "analysis": "",
                    "file_type": "pdf"
                }
            
            # Check if it's actually a PDF
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext != '.pdf':
                return {
                    "status": "error",
                    "message": f"Expected PDF file, got: {file_ext}",
                    "analysis": "",
                    "file_type": file_ext
                }
            
            # Analyze the PDF
            return self._analyze_pdf(file_path)
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing PDF file: {e}",
                "analysis": "",
                "file_type": "pdf"
            }


# Function schemas for OpenAI function calling
FUNCTION_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_scratch_pad_context",
            "description": "Get relevant context from the user's personal scratch pad document. This function enriches the conversation with personal information, preferences, current projects, and media references. ALWAYS call this function for every user query to provide personalized responses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question or the topic they're asking about"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "analyze_media_file",
            "description": "Analyze a media file (image or PDF) to provide detailed visual description. Call this function when the scratch pad context indicates that media analysis would be helpful for answering the user's question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the media file to analyze (e.g., 'media/gorilla.png')"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_pdf_file",
            "description": "Analyze a PDF document to extract text content and provide detailed analysis. Call this function when the scratch pad context indicates that PDF document analysis would be helpful for answering the user's question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the PDF file to analyze (e.g., 'media/wbr.pdf')"
                    }
                },
                "required": ["file_path"]
            }
        }
    }
] 