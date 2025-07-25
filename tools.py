#!/usr/bin/env python3
"""
Function Calling Tools for Luzia

Contains functions that GPT-4.1 can call to enrich conversation context
with scratch pad information and media analysis.
"""

import os
import json
import base64
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
import sympy
import numpy as np


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
                "message": f"Error analyzing media file: {e}",
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
    
    def _parse_expression_safely(self, expression: str) -> sympy.Basic:
        """Safely parse a mathematical expression using SymPy with controlled transformations."""
        try:
            # Clean the expression - remove any potentially dangerous characters
            cleaned_expr = re.sub(r'[^a-zA-Z0-9+\-*/()^=\s\.,_]', '', expression)
            
            # Handle common mathematical notations that users naturally write
            # Convert x^2 to x**2 (exponentiation)
            cleaned_expr = re.sub(r'\^', '**', cleaned_expr)
            
            # Handle implicit multiplication: 3x -> 3*x, but NOT sin(x) -> sin*(x)
            # Pattern: digit followed immediately by single letter (variable)
            cleaned_expr = re.sub(r'(\d)([a-zA-Z])(?![a-zA-Z])', r'\1*\2', cleaned_expr)
            
            # Pattern: closing parenthesis followed by single letter (variable): )x -> )*x
            cleaned_expr = re.sub(r'\)([a-zA-Z])(?![a-zA-Z])', r')*\1', cleaned_expr)
            
            # Pattern: single letter followed by opening parenthesis (NOT function names): x( -> x*(
            # But preserve sin(, cos(, etc. by ensuring the letter is not part of a function name
            cleaned_expr = re.sub(r'(?<![a-zA-Z])([a-zA-Z])\(', r'\1*(', cleaned_expr)
            
            # Use SymPy's parse_expr with minimal transformations for security
            parsed_expr = sympy.parse_expr(
                cleaned_expr, 
                transformations="all",
                evaluate=True
            )
            return parsed_expr
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {e}")
    
    def solve_equation(self, equation: str, variable: str = "x") -> Dict[str, Any]:
        """
        Solve algebraic equations symbolically using SymPy.
        
        Args:
            equation: The equation to solve (e.g., "2*x + 3 = 7" or "x**2 - 4")
            variable: The variable to solve for (default: "x")
            
        Returns:
            Dict containing solutions and metadata
        """
        try:
            # Handle equations with = sign
            if "=" in equation:
                left, right = equation.split("=", 1)
                left_expr = self._parse_expression_safely(left.strip())
                right_expr = self._parse_expression_safely(right.strip())
                expr = left_expr - right_expr
            else:
                # Assume equation equals zero
                expr = self._parse_expression_safely(equation)
            
            # Define the variable
            var = sympy.Symbol(variable)
            
            # Solve the equation
            solutions = sympy.solve(expr, var)
            
            return {
                "status": "success",
                "equation": equation,
                "variable": variable,
                "solutions": [str(sol) for sol in solutions],
                "solution_count": len(solutions),
                "solution_type": "symbolic"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error solving equation '{equation}': {e}",
                "equation": equation,
                "variable": variable
            }
    
    def simplify_expression(self, expression: str) -> Dict[str, Any]:
        """
        Simplify a mathematical expression using SymPy.
        
        Args:
            expression: The expression to simplify
            
        Returns:
            Dict containing simplified expression and metadata
        """
        try:
            expr = self._parse_expression_safely(expression)
            simplified = sympy.simplify(expr)
            
            return {
                "status": "success",
                "original_expression": expression,
                "simplified_expression": str(simplified),
                "is_simplified": str(expr) != str(simplified)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error simplifying expression '{expression}': {e}",
                "original_expression": expression
            }
    
    def calculate_derivative(self, expression: str, variable: str = "x", order: int = 1) -> Dict[str, Any]:
        """
        Calculate the derivative of an expression using SymPy.
        
        Args:
            expression: The expression to differentiate
            variable: The variable to differentiate with respect to
            order: The order of the derivative (default: 1)
            
        Returns:
            Dict containing derivative and metadata
        """
        try:
            expr = self._parse_expression_safely(expression)
            var = sympy.Symbol(variable)
            
            # Calculate derivative
            derivative = sympy.diff(expr, var, order)
            
            return {
                "status": "success",
                "original_expression": expression,
                "variable": variable,
                "order": order,
                "derivative": str(derivative),
                "simplified_derivative": str(sympy.simplify(derivative))
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error calculating derivative of '{expression}': {e}",
                "original_expression": expression,
                "variable": variable,
                "order": order
            }
    
    def calculate_integral(self, expression: str, variable: str = "x", limits: Optional[List] = None) -> Dict[str, Any]:
        """
        Calculate the integral of an expression using SymPy.
        
        Args:
            expression: The expression to integrate
            variable: The variable to integrate with respect to
            limits: Optional list of [lower, upper] limits for definite integral
            
        Returns:
            Dict containing integral and metadata
        """
        try:
            expr = self._parse_expression_safely(expression)
            var = sympy.Symbol(variable)
            
            if limits:
                # Definite integral
                if len(limits) != 2:
                    raise ValueError("Limits must be a list of exactly 2 values [lower, upper]")
                
                lower, upper = limits
                integral = sympy.integrate(expr, (var, lower, upper))
                integral_type = "definite"
            else:
                # Indefinite integral
                integral = sympy.integrate(expr, var)
                integral_type = "indefinite"
            
            return {
                "status": "success",
                "original_expression": expression,
                "variable": variable,
                "limits": limits,
                "integral_type": integral_type,
                "integral": str(integral),
                "simplified_integral": str(sympy.simplify(integral))
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error calculating integral of '{expression}': {e}",
                "original_expression": expression,
                "variable": variable,
                "limits": limits
            }
    
    def factor_expression(self, expression: str) -> Dict[str, Any]:
        """
        Factor a polynomial expression using SymPy.
        
        Args:
            expression: The expression to factor
            
        Returns:
            Dict containing factored expression and metadata
        """
        try:
            expr = self._parse_expression_safely(expression)
            factored = sympy.factor(expr)
            
            return {
                "status": "success",
                "original_expression": expression,
                "factored_expression": str(factored),
                "is_factored": str(expr) != str(factored)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error factoring expression '{expression}': {e}",
                "original_expression": expression
            }
    
    def calculate_complex_arithmetic(self, expression: str) -> Dict[str, Any]:
        """
        Calculate complex arithmetic expressions with high precision.
        Designed for expressions with large numbers (>4 digits) or multiple terms (>3 terms).
        
        Args:
            expression: The arithmetic expression to calculate (e.g., "222222+555555*10000")
            
        Returns:
            Dict containing calculation result and metadata
        """
        try:
            # Clean expression - allow numbers, basic operators, and parentheses
            cleaned_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression.replace('x', '*'))
            
            # Use SymPy for high-precision arithmetic
            expr = sympy.sympify(cleaned_expr)
            result = expr.evalf()  # High precision evaluation
            
            # Convert to Python number for JSON serialization
            if result.is_Integer:
                numeric_result = int(result)
            elif result.is_Float:
                numeric_result = float(result)
            else:
                numeric_result = str(result)
            
            return {
                "status": "success",
                "original_expression": expression,  
                "cleaned_expression": cleaned_expr,
                "result": numeric_result,
                "result_type": "arithmetic",
                "precision": "high"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error calculating arithmetic expression '{expression}': {e}",
                "original_expression": expression
            }
    
    def solve_math(self, query: str) -> Dict[str, Any]:
        """
        Handle all mathematical queries with intelligent routing and optional context.
        
        This function uses a routing LLM to make dual decisions:
        1. Which mathematical operation to perform
        2. Whether user context from scratch pad is needed
        
        Args:
            query: The mathematical question from the user
            
        Returns:
            Dict with mathematical result and routing metadata
        """
        try:
            # Step 1: Load routing prompt
            routing_prompt_file = self.system_prompt_file.replace('system_prompt.txt', 'math_routing_prompt.txt')
            try:
                with open(routing_prompt_file, 'r', encoding='utf-8') as f:
                    routing_system_prompt = f.read().strip()
            except FileNotFoundError:
                return {
                    "status": "error",
                    "message": f"Math routing prompt file not found: {routing_prompt_file}",
                    "query": query
                }
            
            # Step 2: Get routing decision from GPT-4.1-mini (using as placeholder for nano)
            routing_response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini as placeholder for GPT-4.1-nano
                messages=[
                    {"role": "system", "content": routing_system_prompt},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            # Step 3: Parse routing decision
            routing_json = routing_response.choices[0].message.content.strip()
            
            # Clean JSON response (remove any markdown formatting)
            if routing_json.startswith('```'):
                routing_json = routing_json.split('\n')[1:-1]
                routing_json = '\n'.join(routing_json)
            
            try:
                routing_decision = json.loads(routing_json)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "message": f"Invalid JSON from routing LLM: {routing_json}. Error: {e}",
                    "query": query
                }
            
            operation = routing_decision.get("operation")
            needs_context = routing_decision.get("needs_context", False)
            
            if not operation:
                return {
                    "status": "error",
                    "message": f"No operation specified in routing decision: {routing_decision}",
                    "query": query
                }
            
            # Step 4: Get context if needed
            context = ""
            if needs_context:
                context_result = self.get_scratch_pad_context(query)
                if context_result.get("status") == "success":
                    context = context_result.get("relevant_context", "")
            
            # Step 5: Execute specific mathematical operation
            if operation == "solve_equation":
                # Extract equation from query for solve_equation function
                equation_text = self._extract_equation_from_query(query)
                result = self.solve_equation(equation_text)
            elif operation == "simplify_expression":
                # Extract expression from query for simplify_expression function
                expression_text = self._extract_expression_from_query(query)
                result = self.simplify_expression(expression_text)
            elif operation == "calculate_derivative":
                # Extract expression from query for derivative calculation
                expression_text = self._extract_expression_from_query(query)
                # Check for variable and order in query
                variable, order = self._extract_derivative_params(query)
                result = self.calculate_derivative(expression_text, variable, order)
            elif operation == "calculate_integral":
                # Extract expression and limits from query
                expression_text = self._extract_expression_from_query(query)
                variable, limits = self._extract_integral_params(query)
                result = self.calculate_integral(expression_text, variable, limits)
            elif operation == "factor_expression":
                # Extract expression from query for factoring
                expression_text = self._extract_expression_from_query(query)
                result = self.factor_expression(expression_text)
            elif operation == "calculate_complex_arithmetic":
                # Extract arithmetic expression from query
                expression_text = self._extract_arithmetic_from_query(query)
                result = self.calculate_complex_arithmetic(expression_text)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown operation: {operation}",
                    "query": query
                }
            
            # Step 6: Add routing metadata
            result["routing_decision"] = {
                "operation": operation,
                "context_used": needs_context,
                "context_content": context[:100] + "..." if context and len(context) > 100 else context,
                "routing_json": routing_json
            }
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in math routing: {e}",
                "query": query
            }
    
    def _extract_equation_from_query(self, query: str) -> str:
        """Extract the mathematical equation from a natural language query."""
        # Simple extraction - look for mathematical expressions
        # This could be enhanced with more sophisticated parsing
        import re
        
        # Remove common prefixes
        cleaned = re.sub(r'^(solve|find|what is|calculate)\s+', '', query.lower())
        cleaned = re.sub(r'^(the\s+)?(equation|expression)\s+', '', cleaned)
        
        # Look for equation patterns
        equation_match = re.search(r'([0-9a-zA-Z+\-*/^=().\s]+)', cleaned)
        if equation_match:
            return equation_match.group(1).strip()
        
        # Fallback to the original query
        return query
    
    def _extract_expression_from_query(self, query: str) -> str:
        """Extract the mathematical expression from a natural language query."""
        import re
        
        # Remove common prefixes for different operations
        patterns = [
            r'^(simplify|derivative of|differentiate|integrate|factor|factorize)\s+',
            r'^(find the|calculate the|what is the)\s+',
            r'^(the\s+)?(derivative|integral|factor)\s+of\s+'
        ]
        
        cleaned = query.lower()
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # For integrals, remove limits information
        if 'from' in cleaned and 'to' in cleaned:
            # Extract just the expression before "from"
            expr_before_from = cleaned.split('from')[0].strip()
            if expr_before_from:
                cleaned = expr_before_from
        
        # Look for mathematical expressions
        expr_match = re.search(r'([0-9a-zA-Z+\-*/^().\s,sin|cos|tan|log|exp|sqrt]+)', cleaned)
        if expr_match:
            return expr_match.group(1).strip()
        
        # Fallback to the original query
        return query
    
    def _extract_arithmetic_from_query(self, query: str) -> str:
        """Extract arithmetic expression from query."""
        import re
        
        # Look for arithmetic patterns (numbers and basic operators)
        arithmetic_match = re.search(r'([0-9+\-*/().\s]+)', query)
        if arithmetic_match:
            return arithmetic_match.group(1).strip()
        
        return query
    
    def _extract_derivative_params(self, query: str) -> tuple:
        """Extract variable and order from derivative query."""
        import re
        
        # Default values
        variable = "x"
        order = 1
        
        # Look for variable specification
        var_match = re.search(r'with respect to (\w+)', query.lower())
        if var_match:
            variable = var_match.group(1)
        
        # Look for order specification
        order_patterns = [
            r'(\d+)(?:st|nd|rd|th)?\s+derivative',
            r'second derivative',
            r'third derivative'
        ]
        
        for pattern in order_patterns:
            order_match = re.search(pattern, query.lower())
            if order_match:
                if 'second' in pattern:
                    order = 2
                elif 'third' in pattern:
                    order = 3
                else:
                    try:
                        order = int(order_match.group(1))
                    except (IndexError, ValueError):
                        pass
                break
        
        return variable, order
    
    def _extract_integral_params(self, query: str) -> tuple:
        """Extract variable and limits from integral query."""
        import re
        
        # Default values
        variable = "x"
        limits = None
        
        # Look for variable specification
        var_match = re.search(r'with respect to (\w+)', query.lower())
        if var_match:
            variable = var_match.group(1)
        elif re.search(r'd(\w+)', query):
            var_match = re.search(r'd(\w+)', query)
            variable = var_match.group(1)
        
        # Look for limits specification
        limits_patterns = [
            r'from\s+([^to\s]+)\s+to\s+([^\s,]+)',
            r'between\s+([^and\s]+)\s+and\s+([^\s,]+)',
            r'\[([^,]+),\s*([^\]]+)\]'
        ]
        
        for pattern in limits_patterns:
            limits_match = re.search(pattern, query.lower())
            if limits_match:
                try:
                    lower = limits_match.group(1).strip()
                    upper = limits_match.group(2).strip()
                    limits = [lower, upper]
                    break
                except (IndexError, AttributeError):
                    pass
        
        return variable, limits


# Function schemas for OpenAI function calling
FUNCTION_SCHEMAS = [
    {
        "type": "function",
        "function": {
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
        }
    }
] 