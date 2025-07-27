"""
Tools package for Luzia - Refactored Architecture

This package contains focused, single-responsibility tool classes:
- MathTools: Mathematical operations using SymPy
- ScratchPadTools: Context extraction from scratch pad
- MediaTools: Media file analysis
- ToolManager: Coordinates all tools
"""

from .math_tools import MathTools
from .scratchpad_tools import ScratchPadTools as RefactoredScratchPadTools
from .media_tools import MediaTools
from .tool_manager import ToolManager

# Import the backward-compatible wrapper
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    from tools_compat import ScratchPadTools
except ImportError:
    # Fallback: create the backward-compatible interface here
    from typing import Dict, Any, List, Optional
    
    class ScratchPadTools:
        """
        Backward-compatible interface to the refactored tool architecture.
        
        This class maintains the same API as the original monolithic class
        but uses the new clean architecture under the hood.
        """
        
        def __init__(self, scratchpad_file: str = None, system_prompt_file: str = None):
            """Initialize the tools using the new architecture."""
            # Initialize the tool manager which coordinates all specialized tools
            self._manager = ToolManager(scratchpad_file, system_prompt_file)
            
            # Maintain backward compatibility by exposing file paths
            self.scratchpad_file = scratchpad_file or 'scratchpad.txt'
            self.system_prompt_file = system_prompt_file or 'config/system_prompt.txt'
            
            # Expose the OpenAI client for backward compatibility
            self.client = self._manager.math_tools.client
        
        # =============================================================================
        # SCRATCHPAD CONTEXT METHODS
        # =============================================================================
        
        def get_scratch_pad_context(self, query: str) -> Dict[str, Any]:
            """Get relevant context from the scratch pad for a given query."""
            return self._manager.execute_function("get_scratch_pad_context", query=query)
        
        def _load_scratchpad(self) -> str:
            """Load the scratch pad content from file."""
            return self._manager.scratchpad_tools._load_scratchpad()
        
        def _load_system_prompt(self) -> str:
            """Load the system prompt content from file."""
            return self._manager.scratchpad_tools._load_system_prompt()
        
        # =============================================================================
        # MEDIA ANALYSIS METHODS
        # =============================================================================
        
        def analyze_media_file(self, file_path: str) -> Dict[str, Any]:
            """Analyze a media file and return detailed description."""
            return self._manager.execute_function("analyze_media_file", file_path=file_path)
        
        def _encode_image(self, image_path: str) -> str:
            """Encode image to base64 for OpenAI API."""
            return self._manager.media_tools._encode_image(image_path)
        
        def _analyze_image(self, image_path: str) -> Dict[str, Any]:
            """Analyze an image file using GPT-4o-mini vision capabilities."""
            return self._manager.media_tools._analyze_image(image_path)
        
        # =============================================================================
        # MATHEMATICAL METHODS
        # =============================================================================
        
        def solve_math(self, query: str) -> Dict[str, Any]:
            """Handle all mathematical queries with intelligent routing and optional context."""
            return self._manager.execute_function("solve_math", query=query)
        
        def _parse_expression_safely(self, expression: str):
            """Safely parse a mathematical expression using SymPy."""
            return self._manager.math_tools._parse_expression_safely(expression)
        
        def solve_equation(self, equation: str, variable: str = "x") -> Dict[str, Any]:
            """Solve algebraic equations symbolically using SymPy."""
            return self._manager.execute_function("solve_equation", equation=equation, variable=variable)
        
        def simplify_expression(self, expression: str) -> Dict[str, Any]:
            """Simplify a mathematical expression using SymPy."""
            return self._manager.execute_function("simplify_expression", expression=expression)
        
        def calculate_derivative(self, expression: str, variable: str = "x", order: int = 1) -> Dict[str, Any]:
            """Calculate the derivative of an expression using SymPy."""
            return self._manager.execute_function("calculate_derivative", expression=expression, variable=variable, order=order)
        
        def calculate_integral(self, expression: str, variable: str = "x", limits: Optional[List] = None) -> Dict[str, Any]:
            """Calculate the integral of an expression using SymPy."""
            return self._manager.execute_function("calculate_integral", expression=expression, variable=variable, limits=limits)
        
        def factor_expression(self, expression: str) -> Dict[str, Any]:
            """Factor a polynomial expression using SymPy."""
            return self._manager.execute_function("factor_expression", expression=expression)
        
        def calculate_complex_arithmetic(self, expression: str) -> Dict[str, Any]:
            """Calculate complex arithmetic expressions with high precision."""
            return self._manager.execute_function("calculate_complex_arithmetic", expression=expression)
        
        # Helper methods for parameter extraction (maintain backward compatibility)
        def _extract_equation_from_query(self, query: str) -> str:
            """Extract the mathematical equation from a natural language query."""
            return self._manager.math_tools._extract_equation_from_query(query)
        
        def _extract_expression_from_query(self, query: str) -> str:
            """Extract the mathematical expression from a natural language query."""
            return self._manager.math_tools._extract_expression_from_query(query)
        
        def _extract_arithmetic_from_query(self, query: str) -> str:
            """Extract arithmetic expression from query."""
            return self._manager.math_tools._extract_arithmetic_from_query(query)
        
        def _extract_derivative_params(self, query: str) -> tuple:
            """Extract variable and order from derivative query."""
            return self._manager.math_tools._extract_derivative_params(query)
        
        def _extract_integral_params(self, query: str) -> tuple:
            """Extract variable and limits from integral query."""
            return self._manager.math_tools._extract_integral_params(query)
        
        # =============================================================================
        # NEW ARCHITECTURE ACCESS
        # =============================================================================
        
        @property
        def manager(self) -> ToolManager:
            """Direct access to the tool manager for advanced usage."""
            return self._manager
        
        @property
        def math_tools(self):
            """Direct access to math tools."""
            return self._manager.math_tools
        
        @property
        def scratchpad_tools(self):
            """Direct access to scratchpad tools."""
            return self._manager.scratchpad_tools
        
        @property
        def media_tools(self):
            """Direct access to media tools."""
            return self._manager.media_tools

__all__ = [
    'MathTools',
    'RefactoredScratchPadTools', 
    'MediaTools',
    'ToolManager',
    'ScratchPadTools'  # Backward-compatible interface
]

# Function schemas for OpenAI function calling - now generated from ToolManager
FUNCTION_SCHEMAS = ToolManager().get_function_schemas("responses") 