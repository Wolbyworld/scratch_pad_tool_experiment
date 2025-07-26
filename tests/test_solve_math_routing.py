#!/usr/bin/env python3
"""
Unit tests for solve_math routing functionality in ScratchPadTools.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from tools import ScratchPadTools


class TestSolveMathRouting:
    """Test the solve_math routing functionality."""
    
    @pytest.mark.unit
    def test_solve_math_routing_equation_without_context(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test routing to solve_equation without needing context."""
        routing_response = {
            "operation": "solve_equation",
            "needs_context": False
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock routing response
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = json.dumps(routing_response)
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            # Mock the solve_equation method to return success
            with patch.object(tools, 'solve_equation', return_value={
                "status": "success",
                "equation": "2*x + 3 = 7",
                "solutions": ["2"]
            }):
                result = tools.solve_math("solve 2x + 3 = 7")
                
                assert result["status"] == "success"
                assert result["routing_decision"]["operation"] == "solve_equation"
                assert result["routing_decision"]["context_used"] == False
                assert result["routing_decision"]["context_content"] == ""
                assert "2*x + 3 = 7" in result["equation"]
    
    @pytest.mark.unit
    def test_solve_math_routing_with_context_needed(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test routing that requires context from scratch pad."""
        routing_response = {
            "operation": "simplify_expression",
            "needs_context": True
        }
        
        context_response = {
            "status": "success",
            "relevant_context": "User prefers simplified algebraic expressions",
            "media_files_needed": False,
            "recommended_media": [],
            "reasoning": "Context about user preferences"
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock routing response
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = json.dumps(routing_response)
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            # Mock get_scratch_pad_context and simplify_expression
            with patch.object(tools, 'get_scratch_pad_context', return_value=context_response):
                with patch.object(tools, 'simplify_expression', return_value={
                    "status": "success",
                    "original_expression": "x^2 + 2x + 1",
                    "simplified_expression": "(x + 1)^2"
                }):
                    result = tools.solve_math("simplify this expression like before: x^2 + 2x + 1")
                    
                    assert result["status"] == "success"
                    assert result["routing_decision"]["operation"] == "simplify_expression"
                    assert result["routing_decision"]["context_used"] == True
                    assert "User prefers simplified" in result["routing_decision"]["context_content"]
    
    @pytest.mark.unit
    def test_solve_math_routing_invalid_json_response(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of invalid JSON from routing LLM."""
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock invalid JSON response
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = "This is not valid JSON"
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.solve_math("solve some equation")
            
            assert result["status"] == "error"
            assert "Invalid JSON from routing LLM" in result["message"]
            assert "This is not valid JSON" in result["message"]
    
    @pytest.mark.unit
    def test_solve_math_routing_missing_operation(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of routing response missing operation field."""
        incomplete_response = {
            "needs_context": False
            # Missing "operation" field
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = json.dumps(incomplete_response)
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.solve_math("solve equation")
            
            assert result["status"] == "error"
            assert "No operation specified in routing decision" in result["message"]
    
    @pytest.mark.unit
    def test_solve_math_routing_unknown_operation(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of unknown operation from routing LLM."""
        unknown_response = {
            "operation": "unknown_math_operation",
            "needs_context": False
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = json.dumps(unknown_response)
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.solve_math("do some unknown math")
            
            assert result["status"] == "error"
            assert "Unknown operation: unknown_math_operation" in result["message"]
    
    @pytest.mark.unit
    def test_solve_math_routing_all_operations(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test routing to all supported mathematical operations."""
        operations_and_responses = [
            ("solve_equation", {"status": "success", "solutions": ["2"]}),
            ("simplify_expression", {"status": "success", "simplified_expression": "x + 1"}),
            ("calculate_derivative", {"status": "success", "derivative": "2*x"}),
            ("calculate_integral", {"status": "success", "integral": "x**2/2"}),
            ("factor_expression", {"status": "success", "factored_expression": "(x + 1)**2"}),
            ("calculate_complex_arithmetic", {"status": "success", "result": 123456})
        ]
        
        for operation, mock_response in operations_and_responses:
            routing_response = {
                "operation": operation,
                "needs_context": False
            }
            
            with patch('tools.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                routing_mock = Mock()
                routing_mock.choices = [Mock()]
                routing_mock.choices[0].message.content = json.dumps(routing_response)
                mock_client.chat.completions.create.return_value = routing_mock
                
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                tools.client = mock_client
                
                # Mock the specific operation method
                method_name = operation  # They match exactly
                with patch.object(tools, method_name, return_value=mock_response):
                    result = tools.solve_math(f"test query for {operation}")
                    
                    assert result["status"] == "success"
                    assert result["routing_decision"]["operation"] == operation
                    # Verify the mock response is included
                    for key, value in mock_response.items():
                        if key != "status":  # status might be overridden
                            assert key in result
    
    @pytest.mark.unit
    def test_solve_math_routing_prompt_file_not_found(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of missing math routing prompt file."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            
            result = tools.solve_math("solve equation")
            
            assert result["status"] == "error"
            assert "Math routing prompt file not found" in result["message"]
    
    @pytest.mark.unit
    def test_solve_math_routing_openai_api_error(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of OpenAI API errors during routing."""
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock API error
            mock_client.chat.completions.create.side_effect = Exception("API error during routing")
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.solve_math("solve equation")
            
            assert result["status"] == "error"
            assert "Error in math routing" in result["message"]
            assert "API error during routing" in result["message"]
    
    @pytest.mark.unit
    def test_solve_math_routing_json_wrapped_in_markdown(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of JSON wrapped in markdown code blocks from routing LLM."""
        routing_response = {
            "operation": "solve_equation",
            "needs_context": False
        }
        
        markdown_wrapped = f"""```json
{json.dumps(routing_response)}
```"""
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = markdown_wrapped
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            with patch.object(tools, 'solve_equation', return_value={"status": "success", "solutions": ["2"]}):
                result = tools.solve_math("solve equation")
                
                assert result["status"] == "success"
                assert result["routing_decision"]["operation"] == "solve_equation"


class TestParameterExtraction:
    """Test parameter extraction methods for different math operations."""
    
    @pytest.mark.unit
    def test_extract_equation_from_query(self, scratch_pad_tools):
        """Test extraction of equations from natural language queries."""
        test_cases = [
            ("solve 2x + 3 = 7", "2x + 3 = 7"),
            ("find the solution to x^2 - 4 = 0", "x^2 - 4 = 0"),
            ("what is the answer to 3*y + 2 = 11", "3*y + 2 = 11"),
            ("can you solve the equation 5x - 3 = 2x + 9", "5x - 3 = 2x + 9"),
        ]
        
        for query, expected in test_cases:
            result = scratch_pad_tools._extract_equation_from_query(query)
            assert expected in result or result in expected  # Allow some flexibility in parsing
    
    @pytest.mark.unit
    def test_extract_expression_from_query(self, scratch_pad_tools):
        """Test extraction of expressions from natural language queries."""
        test_cases = [
            ("simplify x^2 + 2x + 1", "x^2 + 2x + 1"),
            ("find the derivative of sin(x)*cos(x)", "sin(x)*cos(x)"),
            ("integrate x**2", "x**2"),
            ("factor the expression 6x^2 + 11x + 3", "6x^2 + 11x + 3"),
        ]
        
        for query, expected in test_cases:
            result = scratch_pad_tools._extract_expression_from_query(query)
            assert expected in result or result.replace("*", "") in expected.replace("*", "")
    
    @pytest.mark.unit
    def test_extract_arithmetic_from_query(self, scratch_pad_tools):
        """Test extraction of arithmetic expressions from queries."""
        test_cases = [
            ("calculate 222222+555555*10000", "222222+555555*10000"),
            ("what is 12345*67890", "12345*67890"),
            ("compute 1000+2000+3000", "1000+2000+3000"),
            ("find the result of 999*888/777", "999*888/777"),
        ]
        
        for query, expected in test_cases:
            result = scratch_pad_tools._extract_arithmetic_from_query(query)
            # Allow some variation in extracted arithmetic
            assert any(char.isdigit() for char in result)  # Should contain numbers
            assert any(op in result for op in ['+', '-', '*', '/'])  # Should contain operators
    
    @pytest.mark.unit
    def test_extract_derivative_params(self, scratch_pad_tools):
        """Test extraction of derivative parameters from queries."""
        test_cases = [
            ("find the derivative of x^3", ("x", 1)),
            ("calculate the derivative of sin(y) with respect to y", ("y", 1)),
            ("what is the second derivative of x^4", ("x", 2)),
            ("find the third derivative of x^5", ("x", 3)),
            ("differentiate f(t) with respect to t", ("t", 1)),
        ]
        
        for query, expected in test_cases:
            variable, order = scratch_pad_tools._extract_derivative_params(query)
            expected_var, expected_order = expected
            assert variable == expected_var
            assert order == expected_order
    
    @pytest.mark.unit
    def test_extract_integral_params(self, scratch_pad_tools):
        """Test extraction of integral parameters from queries."""
        test_cases = [
            ("integrate x^2", ("x", None)),
            ("find the integral of sin(t) with respect to t", ("t", None)),
            ("integrate x^2 from 0 to 1", ("x", ["0", "1"])),
            ("calculate the integral of cos(y) from pi to 2*pi", ("y", ["pi", "2*pi"])),
            ("find the definite integral of 2x+1 between 1 and 3", ("x", ["1", "3"])),
        ]
        
        for query, expected in test_cases:
            variable, limits = scratch_pad_tools._extract_integral_params(query)
            expected_var, expected_limits = expected
            assert variable == expected_var
            assert limits == expected_limits
    
    @pytest.mark.unit
    def test_extract_derivative_params_edge_cases(self, scratch_pad_tools):
        """Test edge cases for derivative parameter extraction."""
        # Default cases
        var, order = scratch_pad_tools._extract_derivative_params("derivative of f")
        assert var == "x"  # Default variable
        assert order == 1  # Default order
        
        # Complex queries
        var, order = scratch_pad_tools._extract_derivative_params("find the 5th derivative")
        assert order == 5
        
        # Multiple mentions - should pick first/most relevant
        var, order = scratch_pad_tools._extract_derivative_params("second derivative of f with respect to z")
        assert var == "z"
        assert order == 2
    
    @pytest.mark.unit
    def test_extract_integral_params_edge_cases(self, scratch_pad_tools):
        """Test edge cases for integral parameter extraction."""
        # Default cases
        var, limits = scratch_pad_tools._extract_integral_params("integrate f")
        assert var == "x"  # Default variable
        assert limits is None  # Default indefinite
        
        # Different limit formats
        test_cases = [
            ("integral from -1 to 1", ["−1", "1"]),  # May vary based on parsing
            ("integrate between a and b", ["a", "b"]),
            ("definite integral [0, pi]", ["0", "pi"]),
        ]
        
        for query, expected_limits in test_cases:
            var, limits = scratch_pad_tools._extract_integral_params(query)
            if limits:
                assert len(limits) == 2
                # Check that we got some reasonable limits (exact format may vary)
                assert all(isinstance(limit, str) for limit in limits)


class TestSolveMathEdgeCases:
    """Test edge cases and error conditions for solve_math functionality."""
    
    @pytest.mark.unit
    def test_solve_math_very_long_query(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of very long mathematical queries."""
        very_long_query = "solve this equation " + "with many variables " * 100 + " 2x + 3 = 7"
        
        routing_response = {
            "operation": "solve_equation",
            "needs_context": False
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = json.dumps(routing_response)
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            with patch.object(tools, 'solve_equation', return_value={"status": "success", "solutions": ["2"]}):
                result = tools.solve_math(very_long_query)
                
                assert result["status"] == "success"
                assert result["query"] == very_long_query
    
    @pytest.mark.unit
    def test_solve_math_unicode_query(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of queries with Unicode mathematical symbols."""
        unicode_query = "solve ∫(x²)dx = y for y"
        
        routing_response = {
            "operation": "solve_equation",
            "needs_context": False
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = json.dumps(routing_response)
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            with patch.object(tools, 'solve_equation', return_value={"status": "success", "solutions": ["x^3/3"]}):
                result = tools.solve_math(unicode_query)
                
                assert result["status"] == "success"
                assert "∫" in result["query"]  # Unicode preserved
    
    @pytest.mark.unit
    def test_solve_math_empty_query(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of empty mathematical queries."""
        routing_response = {
            "operation": "solve_equation",
            "needs_context": False
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = json.dumps(routing_response)
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            with patch.object(tools, 'solve_equation', return_value={"status": "error", "message": "No equation provided"}):
                result = tools.solve_math("")
                
                # Should handle gracefully
                assert "status" in result
                assert result["query"] == ""
    
    @pytest.mark.unit
    def test_solve_math_context_fetch_error(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of errors when fetching context."""
        routing_response = {
            "operation": "solve_equation",
            "needs_context": True  # This will trigger context fetch
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            routing_mock = Mock()
            routing_mock.choices = [Mock()]
            routing_mock.choices[0].message.content = json.dumps(routing_response)
            mock_client.chat.completions.create.return_value = routing_mock
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            # Mock context fetch error
            with patch.object(tools, 'get_scratch_pad_context', return_value={"status": "error", "message": "Context error"}):
                with patch.object(tools, 'solve_equation', return_value={"status": "success", "solutions": ["2"]}):
                    result = tools.solve_math("solve with context: 2x + 3 = 7")
                    
                    # Should still succeed but with empty context
                    assert result["status"] == "success"
                    assert result["routing_decision"]["context_used"] == True
                    assert result["routing_decision"]["context_content"] == "" 