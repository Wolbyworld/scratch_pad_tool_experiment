#!/usr/bin/env python3
"""
Pytest fixtures and configuration for Luzia tests.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any


@pytest.fixture
def temp_scratchpad_file():
    """Create a temporary scratchpad file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
USER FACTS:
- User is learning Python programming
- User prefers working with examples
- User has experience with basic mathematics

MEDIA-DOCUMENT SUMMARIES:
- gorilla.png: Artistic image of a gorilla performing a slam dunk in what appears to be a basketball setting
- sample.jpg: A sample image for testing purposes

CONVERSATION HISTORY:
- Previous discussion about mathematical problem-solving tools
- User asked about SymPy integration for deterministic calculations
""")
        temp_file_path = f.name
    
    yield temp_file_path
    
    # Cleanup
    try:
        os.unlink(temp_file_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_system_prompt_file():
    """Create a temporary system prompt file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""⚠️ CRITICAL MATHEMATICAL QUERIES RULE - HIGHEST PRIORITY ⚠️
🚨 MANDATORY FOR ALL MATHEMATICAL PROBLEMS 🚨

- For ANY mathematical query (equations, calculations, derivatives, integrals, algebra, arithmetic, etc.):
  - ❌ DO NOT solve the mathematical problem yourself
  - ❌ DO NOT provide mathematical solutions, steps, or hints
  - ❌ DO NOT explain how to solve it
  - ✅ ALWAYS respond exactly: "Mathematical calculation required - specific tools needed for: [brief description]"
  - This is MANDATORY to ensure mathematical functions are called instead of manual solutions

Examples:
- Query: "solve 2x + 3 = 7" → Response: "Mathematical calculation required - specific tools needed for: solving linear equation"
- Query: "what's 123 * 456" → Response: "Mathematical calculation required - specific tools needed for: arithmetic calculation"  
- Query: "derivative of x^2" → Response: "Mathematical calculation required - specific tools needed for: calculus derivative"

====================================================================

You are a personal knowledge assistant. Given a user's query and their scratch-pad document, extract and return the most relevant context to help answer their question.

LOOK-UP ORDER
A. USER FACTS → B. MEDIA-DOCUMENT SUMMARIES → C. MEDIA FILES""")
        temp_file_path = f.name
    
    yield temp_file_path
    
    # Cleanup
    try:
        os.unlink(temp_file_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def scratch_pad_tools(temp_scratchpad_file, temp_system_prompt_file):
    """Create ScratchPadTools instance with temporary files."""
    from tools.scratchpad_tools import ScratchPadTools
    return ScratchPadTools(
        scratchpad_file=temp_scratchpad_file,
        system_prompt_file=temp_system_prompt_file
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for all tool modules."""
    with patch('tools.scratchpad_tools.OpenAI') as mock_scratchpad_openai, \
         patch('tools.math_tools.OpenAI') as mock_math_openai, \
         patch('tools.media_tools.OpenAI') as mock_media_openai:
        
        # Create mock instances
        mock_client = MagicMock()
        mock_scratchpad_openai.return_value = mock_client
        mock_math_openai.return_value = mock_client
        mock_media_openai.return_value = mock_client
        
        # Mock the responses.create method
        mock_response = MagicMock()
        mock_response.output_text = '{"relevant_context": "Test context", "media_files_needed": false, "recommended_media": [], "reasoning": "Test reasoning"}'
        mock_response.output = []
        mock_client.responses.create.return_value = mock_response
        
        yield mock_client


@pytest.fixture  
def mock_openai_math_routing():
    """Mock OpenAI client specifically for math routing tests."""
    with patch('tools.math_tools.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock math routing response
        mock_response = MagicMock()
        mock_response.output_text = '{"operation": "solve_equation", "needs_context": false, "query": "2x + 3 = 7"}'
        mock_response.output = []
        mock_client.responses.create.return_value = mock_response
        
        yield mock_client


@pytest.fixture
def sample_test_cases():
    """Sample test cases for mathematical operations."""
    return {
        "equations": [
            ("2*x + 3 = 7", ["2"]),
            ("x^2 - 4 = 0", ["-2", "2"]),
            ("x + 1 = 0", ["-1"])
        ],
        "expressions": [
            ("2*x + 3*x", "5*x"),
            ("x^2 + 2*x + 1", "(x + 1)**2"),
            ("sin(x)^2 + cos(x)^2", "1")
        ],
        "derivatives": [
            ("x^2", "2*x"),
            ("sin(x)", "cos(x)"),
            ("e^x", "exp(x)")
        ],
        "integrals": [
            ("x", "x**2/2"),
            ("2*x", "x**2"),
            ("x^2", "x**3/3")
        ]
    }


@pytest.fixture
def setup_test_environment(temp_scratchpad_file, temp_system_prompt_file):
    """Set up complete test environment with all necessary files."""
    # Create temporary math routing prompt file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""You are a mathematical query classifier. Given a user's mathematical query, determine:

1. The specific mathematical operation needed
2. Whether user context is needed for personalization

Respond with JSON:
{
    "operation": "solve_equation|simplify_expression|calculate_derivative|calculate_integral|factor_expression|calculate_complex_arithmetic",
    "needs_context": true/false,
    "query": "cleaned mathematical expression"
}

Examples:
- "solve 2x + 3 = 7" → {"operation": "solve_equation", "needs_context": false, "query": "2x + 3 = 7"}
- "derivative of x^2" → {"operation": "calculate_derivative", "needs_context": false, "query": "x^2"}
- "solve this like before: x + 1 = 0" → {"operation": "solve_equation", "needs_context": true, "query": "x + 1 = 0"}""")
        math_routing_prompt_file = f.name
    
    yield {
        'scratchpad_file': temp_scratchpad_file,
        'system_prompt_file': temp_system_prompt_file,
        'math_routing_prompt_file': math_routing_prompt_file
    }
    
    # Cleanup
    try:
        os.unlink(math_routing_prompt_file)
    except FileNotFoundError:
        pass 