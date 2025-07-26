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