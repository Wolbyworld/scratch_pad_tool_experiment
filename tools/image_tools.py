#!/usr/bin/env python3
"""
Image Generation Tools for Luzia

Focused on image generation and prompt enhancement using DALL-E and GPT-4.1-mini.
Single responsibility: image generation and prompt optimization only.
"""

import os
import uuid
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI


class ImageTools:
    """Focused image generation functionality."""
    
    def __init__(self):
        """Initialize the image generation tools."""
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        
        # Ensure media directory exists
        self.media_dir = "media"
        os.makedirs(self.media_dir, exist_ok=True)
    
    def improve_prompt(self, original_prompt: str, additional_instructions: str = "") -> Dict[str, Any]:
        """
        Enhance a user's image generation prompt using GPT-4.1-mini.
        
        Args:
            original_prompt: The user's original image generation request
            additional_instructions: Optional additional instructions for the prompt
            
        Returns:
            Dict containing the improved prompt and metadata
        """
        try:
            # Create system prompt for prompt enhancement
            system_prompt = """You are a prompt enhancement specialist for image generation. Your job is to improve user prompts to create better, more detailed, and visually appealing images.

Guidelines:
- Keep the core intent and subject of the original prompt
- Add artistic style, composition, lighting, and detail suggestions
- Make the prompt more specific and visually descriptive
- Don't completely change the user's original concept
- Add professional photography/art terminology when appropriate
- Keep it concise but descriptive (aim for 1-3 sentences)

Return only the improved prompt, nothing else."""

            # Create user message
            user_message = f"Original prompt: {original_prompt}"
            if additional_instructions:
                user_message += f"\nAdditional instructions: {additional_instructions}"
            
            # Call GPT-4.1-mini for prompt improvement
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4o-mini as specified in the requirements
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            improved_prompt = response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "original_prompt": original_prompt,
                "additional_instructions": additional_instructions,
                "improved_prompt": improved_prompt
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error improving prompt: {e}",
                "original_prompt": original_prompt,
                "improved_prompt": original_prompt  # Fallback to original
            }
    
    def generate_image(self, prompt: str, improve_prompt: bool = True, additional_instructions: str = "") -> Dict[str, Any]:
        """
        Generate an image using DALL-E with optional prompt improvement.
        
        Args:
            prompt: The image generation prompt
            improve_prompt: Whether to enhance the prompt first
            additional_instructions: Additional instructions for prompt enhancement
            
        Returns:
            Dict containing image generation results and metadata
        """
        try:
            # Step 1: Improve prompt if requested
            final_prompt = prompt
            prompt_data = None
            
            if improve_prompt:
                prompt_result = self.improve_prompt(prompt, additional_instructions)
                if prompt_result["status"] == "success":
                    final_prompt = prompt_result["improved_prompt"]
                    prompt_data = prompt_result
                else:
                    # If prompt improvement fails, continue with original
                    prompt_data = {
                        "status": "error",
                        "original_prompt": prompt,
                        "improved_prompt": prompt,
                        "error": prompt_result.get("message", "Prompt improvement failed")
                    }
            
            # Step 2: Generate image with DALL-E
            dalle_response = self.client.images.generate(
                model="dall-e-3",
                prompt=final_prompt,
                size="1024x1024",  # Standard size
                quality="standard",  # Cost-effective setting as requested
                n=1
            )
            
            # Step 3: Download and save the image
            image_url = dalle_response.data[0].url
            
            # Generate unique filename
            image_id = str(uuid.uuid4())[:8]
            filename = f"generated_{image_id}.png"
            file_path = os.path.join(self.media_dir, filename)
            
            # Download image
            import requests
            response = requests.get(image_url)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return {
                "status": "success",
                "file_path": file_path,
                "filename": filename,
                "original_prompt": prompt,
                "final_prompt": final_prompt,
                "prompt_improvement": prompt_data,
                "image_url": image_url,
                "image_id": image_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating image: {e}",
                "original_prompt": prompt,
                "file_path": None
            }
    
    def generate_image_with_context(self, user_request: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate an image incorporating context from previous interactions or scratchpad.
        This is used for "fake editing" functionality.
        
        Args:
            user_request: The user's current request (could be edit or new generation)
            context_data: Context from scratchpad or previous interactions
            
        Returns:
            Dict containing image generation results
        """
        try:
            # Extract relevant context for prompt enhancement
            additional_instructions = ""
            
            if context_data:
                # Extract previous image descriptions, prompts, etc.
                if "previous_prompts" in context_data:
                    additional_instructions += f"Build upon previous image concepts: {context_data['previous_prompts']}. "
                
                if "edit_request" in context_data:
                    additional_instructions += f"Apply these modifications: {context_data['edit_request']}. "
                
                if "style_preferences" in context_data:
                    additional_instructions += f"Maintain style: {context_data['style_preferences']}. "
            
            # Generate image with context-aware prompt improvement
            return self.generate_image(
                prompt=user_request,
                improve_prompt=True,
                additional_instructions=additional_instructions.strip()
            )
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating image with context: {e}",
                "user_request": user_request
            }