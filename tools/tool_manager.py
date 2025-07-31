#!/usr/bin/env python3
"""
Tool Manager for Luzia

Coordinates all specialized tool classes and provides a unified interface.
Acts as the main entry point for all tool operations.
"""

from typing import Dict, Any
from .math_tools import MathTools
from .scratchpad_tools import ScratchPadTools
from .media_tools import MediaTools
from .image_tools import ImageTools


class ToolManager:
    """Coordinates all tools - single entry point for tool operations."""
    
    def __init__(self, scratchpad_file: str = None, system_prompt_file: str = None):
        """Initialize all tool components.
        
        Args:
            scratchpad_file: Path to scratch pad file
            system_prompt_file: Path to system prompt file
        """
        # Initialize all specialized tools
        self.math_tools = MathTools()
        self.scratchpad_tools = ScratchPadTools(scratchpad_file, system_prompt_file)
        self.media_tools = MediaTools()
        self.image_tools = ImageTools()
    
    def execute_function(self, function_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a function by name with the appropriate tool.
        
        Args:
            function_name: Name of the function to execute
            **kwargs: Arguments to pass to the function
            
        Returns:
            Dict containing the function result
        """
        if function_name == "get_scratch_pad_context":
            return self.scratchpad_tools.get_scratch_pad_context(**kwargs)
        
        elif function_name == "analyze_media_file":
            return self.media_tools.analyze_media_file(**kwargs)
        
        elif function_name == "solve_math":
            # Pass the context fetcher function to math tools for optional context
            context_fetcher = self.scratchpad_tools.get_scratch_pad_context
            return self.math_tools.solve_math(context_fetcher_func=context_fetcher, **kwargs)
        
        # Individual math functions (for direct access if needed)
        elif function_name == "solve_equation":
            return self.math_tools.solve_equation(**kwargs)
        
        elif function_name == "simplify_expression":
            return self.math_tools.simplify_expression(**kwargs)
        
        elif function_name == "calculate_derivative":
            return self.math_tools.calculate_derivative(**kwargs)
        
        elif function_name == "calculate_integral":
            return self.math_tools.calculate_integral(**kwargs)
        
        elif function_name == "factor_expression":
            return self.math_tools.factor_expression(**kwargs)
        
        elif function_name == "calculate_complex_arithmetic":
            return self.math_tools.calculate_complex_arithmetic(**kwargs)
        
        # Image generation functions
        elif function_name == "generate_image":
            return self.image_tools.generate_image(**kwargs)
        
        elif function_name == "improve_prompt":
            return self.image_tools.improve_prompt(**kwargs)
        
        elif function_name == "generate_image_with_context":
            return self.image_tools.generate_image_with_context(**kwargs)
        
        else:
            return {
                "status": "error",
                "message": f"Unknown function: {function_name}",
                "function_name": function_name
            }
    
    def get_function_schemas(self, api_format: str = "responses") -> list:
        """Get the function schemas for OpenAI function calling.
        
        Args:
            api_format: Either "responses" for Responses API or "chat" for Chat Completions API
            
        Returns:
            List of function schemas in the specified format
        """
        base_schemas = [
            {
                "type": "function",
                "name": "get_scratch_pad_context",
                "description": "Get relevant context from the user's personal scratch pad document. Use for non-mathematical queries or when personal context is specifically needed. For mathematical queries, use solve_math instead.",
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
            },
            {
                "type": "function",
                "name": "analyze_media_file",
                "description": "Analyze a media file (image or PDF) to provide detailed visual description. Call this function when the scratch pad context indicates that media analysis would be helpful for answering the user's question.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the media file to analyze (e.g., 'media/gorilla.png')"
                        },
                        "user_question": {
                            "type": "string",
                            "description": "The specific question the user is asking that requires media analysis (optional but recommended for context-aware analysis)",
                            "default": ""
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "type": "function",
                "name": "solve_math",
                "description": "Handle ALL mathematical queries including equations, derivatives, integrals, simplification, factoring, and complex arithmetic. This function intelligently routes to the appropriate mathematical operation and only fetches user context when needed for personalization. Use this for ANY mathematical request.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The complete mathematical question or problem to solve. Examples: 'solve 2x+3=7', 'derivative of x^2', 'simplify sin^2+cos^2', 'factor x^2+2x+1', '222222+555555*10000', 'integrate x^2 from 0 to 1'. Include any context like 'solve this like before' for personalized responses."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "type": "function",
                "name": "generate_image",
                "description": "Generate an image using DALL-E. Use this when the user requests image creation, generation, or visual content. The function automatically improves prompts for better results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The image generation prompt describing what to create"
                        },
                        "improve_prompt": {
                            "type": "boolean",
                            "description": "Whether to enhance the prompt automatically (default: true)",
                            "default": True
                        },
                        "additional_instructions": {
                            "type": "string",
                            "description": "Additional instructions for prompt enhancement (optional)",
                            "default": ""
                        }
                    },
                    "required": ["prompt"]
                }
            }
        ]
        
        # Convert to Chat Completions format if requested
        if api_format == "chat":
            return [{
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": schema["parameters"]
                }
            } for schema in base_schemas]
        
        return base_schemas
    
    # Convenience methods for direct access to individual tools
    @property
    def math(self) -> MathTools:
        """Direct access to math tools."""
        return self.math_tools
    
    @property
    def scratchpad(self) -> ScratchPadTools:
        """Direct access to scratchpad tools."""
        return self.scratchpad_tools
    
    @property
    def media(self) -> MediaTools:
        """Direct access to media tools."""
        return self.media_tools
    
    @property
    def image(self) -> ImageTools:
        """Direct access to image tools."""
        return self.image_tools 