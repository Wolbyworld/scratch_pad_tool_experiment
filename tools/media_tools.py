#!/usr/bin/env python3
"""
Media Tools for Luzia

Focused on analyzing media files (images, PDFs) and providing detailed descriptions.
Single responsibility: media file analysis only.
"""

import os
import base64
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI


class MediaTools:
    """Focused media file analysis functionality."""
    
    def __init__(self):
        """Initialize the media tools."""
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for OpenAI API."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            return f"Error encoding image: {e}"
    
    def analyze_media_file(self, file_path: str, user_question: str = None) -> Dict[str, Any]:
        """
        Analyze a media file (image) and return detailed description.
        This function is called when the scratch pad indicates media analysis is needed.
        
        Args:
            file_path: Path to the media file to analyze
            user_question: The specific question the user is asking about this media (optional)
            
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
                return self._analyze_image(file_path, user_question)
            elif file_ext == '.pdf':
                # For now, return basic info for PDFs (can be enhanced later)
                return {
                    "status": "success",
                    "file_path": file_path,
                    "file_type": "pdf",
                    "analysis": "PDF file detected. Visual content analysis not yet implemented for PDFs.",
                    "recommendation": "Use the text summary from the scratch pad for PDF content."
                }
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
                "message": f"Error analyzing image: {e}",
                "analysis": "",
                "file_type": "unknown"
            }
    
    def _analyze_image(self, image_path: str, user_question: str = None) -> Dict[str, Any]:
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
            
            # Create context-aware prompt based on user question
            if user_question:
                # Create a specific prompt based on the user's question
                if any(word in user_question.lower() for word in ['count', 'how many', 'number of']):
                    analysis_prompt = f"The user is asking: '{user_question}'. Please count and provide the exact number of items they're asking about in this image. Be specific and precise with your count."
                elif any(word in user_question.lower() for word in ['what color', 'color of', 'colors']):
                    analysis_prompt = f"The user is asking: '{user_question}'. Please focus on describing the colors in this image, being specific about the hues, shades, and color relationships you observe."
                elif any(word in user_question.lower() for word in ['where', 'location', 'position']):
                    analysis_prompt = f"The user is asking: '{user_question}'. Please focus on describing the locations and positions of objects in this image."
                elif any(word in user_question.lower() for word in ['what is', 'what are', 'describe', 'tell me about']):
                    analysis_prompt = f"The user is asking: '{user_question}'. Please provide a detailed description focusing on what they're specifically asking about in this image."
                else:
                    analysis_prompt = f"The user is asking: '{user_question}'. Please analyze this image with a focus on answering their specific question. Provide relevant details that directly address what they want to know."
            else:
                # Default general analysis prompt
                analysis_prompt = "Analyze this image in detail. Describe what you see, including objects, people, text, colors, composition, and any other relevant details that would be helpful for someone asking about this image."
            
            # Analyze image with GPT-4o-mini using Chat Completions API (required for vision)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": analysis_prompt
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