#!/usr/bin/env python3
"""
Pytest fixtures and configuration for Luzia tests.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from tools import ScratchPadTools


@pytest.fixture
def temp_scratchpad_file():
    """Create a temporary scratchpad file for testing."""
    content = """
# Test Scratchpad Content

## Personal Information
- Name: Test User
- Preferences: CLI tools, testing
- Current projects: Math calculator integration

## Notes
- Working on SymPy integration
- Testing mathematical functions
- Building test coverage

## Media Files
- media/test_image.png: Test image for analysis
- media/gorilla.png: Gorilla image for vision testing
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    
    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def temp_system_prompt_file():
    """Create a temporary system prompt file for testing."""
    content = """
You are a test system prompt for context extraction.
Extract relevant information and return JSON format:
{
    "relevant_context": "extracted information",
    "media_files_needed": true/false,
    "recommended_media": ["file1", "file2"],
    "reasoning": "explanation"
}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    
    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def temp_math_routing_prompt_file(temp_system_prompt_file):
    """Create a temporary math routing prompt file."""
    content = """
You are a mathematical query classifier. Return JSON with:
{
    "operation": "solve_equation|simplify_expression|calculate_derivative|calculate_integral|factor_expression|calculate_complex_arithmetic",
    "needs_context": true/false
}

Examples:
- "solve 2x+3=7" → {"operation": "solve_equation", "needs_context": false}
- "simplify x^2+2x+1" → {"operation": "simplify_expression", "needs_context": false}
"""
    
    routing_file = temp_system_prompt_file.replace('system_prompt.txt', 'math_routing_prompt.txt')
    with open(routing_file, 'w') as f:
        f.write(content)
    
    yield routing_file
    
    # Cleanup
    if os.path.exists(routing_file):
        os.unlink(routing_file)


@pytest.fixture
def temp_image_file():
    """Create a temporary test image file."""
    # Create a simple 1x1 PNG image (minimal valid PNG)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(png_data)
        f.flush()
        yield f.name
    
    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def scratch_pad_tools(temp_scratchpad_file, temp_system_prompt_file):
    """Create ScratchPadTools instance with temporary files."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
        tools = ScratchPadTools(
            scratchpad_file=temp_scratchpad_file,
            system_prompt_file=temp_system_prompt_file
        )
        yield tools


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    # Patch OpenAI in all the individual tool modules
    with patch('tools.math_tools.OpenAI') as mock_math_openai, \
         patch('tools.scratchpad_tools.OpenAI') as mock_scratchpad_openai, \
         patch('tools.media_tools.OpenAI') as mock_media_openai:
        
        mock_client = Mock()
        mock_math_openai.return_value = mock_client
        mock_scratchpad_openai.return_value = mock_client
        mock_media_openai.return_value = mock_client
        
        # Default successful response for Responses API
        mock_response = Mock()
        mock_response.output_text = json.dumps({
            "relevant_context": "Test context extracted",
            "media_files_needed": False,
            "recommended_media": [],
            "reasoning": "No media needed for this query"
        })
        # Mock output structure for function calls
        mock_response.output = []
        
        mock_client.responses.create.return_value = mock_response
        
        yield mock_client


@pytest.fixture
def mock_openai_math_routing():
    """Mock OpenAI client specifically for math routing responses."""
    mock_response = Mock()
    mock_response.output_text = json.dumps({
        "operation": "solve_equation",
        "needs_context": False
    })
    mock_response.output = []
    return mock_response


@pytest.fixture
def sample_test_cases():
    """Sample test cases for mathematical functions."""
    return {
        "equations": [
            ("2*x + 3 = 7", "x", ["2"]),
            ("x**2 - 4 = 0", "x", ["-2", "2"]),
            ("x = x", "x", [])  # Identity equation
        ],
        "expressions": [
            ("x**2 + 2*x + 1", "(x + 1)**2"),
            ("sin(x)**2 + cos(x)**2", "1"),
            ("sqrt(x**2)", "sqrt(x**2)")
        ],
        "derivatives": [
            ("x**3", "x", 1, "3*x**2"),
            ("sin(x)*cos(x)", "x", 1, "cos(2*x)"),
            ("x**4", "x", 2, "12*x**2")
        ],
        "integrals": [
            ("x**2", "x", None, "x**3/3"),
            ("sin(x)", "x", ["0", "pi"], "2")
        ],
        "factors": [
            ("x**2 + 2*x + 1", "(x + 1)**2"),
            ("x**3 - 8", "(x - 2)*(x**2 + 2*x + 4)")
        ],
        "arithmetic": [
            ("222222+555555*10000", 5555772222),
            ("12345*67890", 838102050),
            ("1000+2000+3000", 6000)
        ]
    }


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-api-key-12345',
        'SCRATCHPAD_FILE': 'test_scratchpad.txt',
        'SYSTEM_PROMPT_FILE': 'config/test_system_prompt.txt'
    }):
        yield 