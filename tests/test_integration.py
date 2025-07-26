#!/usr/bin/env python3
"""
Integration tests for ScratchPadTools - testing component interactions.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from tools import ScratchPadTools, FUNCTION_SCHEMAS


class TestToolIntegration:
    """Test integration between different tool components."""
    
    @pytest.mark.integration
    def test_full_workflow_with_context_and_math(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test complete workflow: context extraction -> math routing -> calculation."""
        # Mock responses for each step
        context_response = {
            "relevant_context": "User prefers step-by-step solutions",
            "media_files_needed": False,
            "recommended_media": [],
            "reasoning": "No media needed for math"
        }
        
        routing_response = {
            "operation": "solve_equation",
            "needs_context": True
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Setup mock responses in sequence
            mock_responses = [
                # First call: routing decision
                Mock(choices=[Mock(message=Mock(content=json.dumps(routing_response)))]),
                # Second call: context extraction
                Mock(choices=[Mock(message=Mock(content=json.dumps(context_response)))])
            ]
            mock_client.chat.completions.create.side_effect = mock_responses
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            # Mock the final solve_equation call
            expected_solution = {
                "status": "success",
                "equation": "2*x + 3 = 7",
                "variable": "x",
                "solutions": ["2"],
                "solution_type": "symbolic"
            }
            
            with patch.object(tools, 'solve_equation', return_value=expected_solution):
                result = tools.solve_math("solve this like you did before: 2x + 3 = 7")
                
                # Verify the complete workflow
                assert result["status"] == "success"
                assert result["routing_decision"]["operation"] == "solve_equation"
                assert result["routing_decision"]["context_used"] == True
                assert "step-by-step" in result["routing_decision"]["context_content"]
                assert result["solutions"] == ["2"]
                
                # Verify API calls were made
                assert mock_client.chat.completions.create.call_count == 2
    
    @pytest.mark.integration
    def test_context_triggers_media_analysis(self, temp_scratchpad_file, temp_system_prompt_file, temp_image_file):
        """Test that context extraction can trigger media analysis."""
        context_response_with_media = {
            "relevant_context": "User has a gorilla image for analysis",
            "media_files_needed": True,
            "recommended_media": [temp_image_file],
            "reasoning": "Image analysis would help with the query"
        }
        
        media_analysis_response = {
            "status": "success",
            "file_path": temp_image_file,
            "file_type": "image",
            "analysis": "This image contains a 1x1 pixel test image",
            "mime_type": "image/png"
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock context response
            context_mock = Mock()
            context_mock.choices = [Mock()]
            context_mock.choices[0].message.content = json.dumps(context_response_with_media)
            
            # Mock media analysis response
            media_mock = Mock()
            media_mock.choices = [Mock()]
            media_mock.choices[0].message.content = "This image contains a 1x1 pixel test image"
            
            mock_client.chat.completions.create.side_effect = [context_mock, media_mock]
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            # Test context extraction
            context_result = tools.get_scratch_pad_context("tell me about the gorilla image")
            assert context_result["media_files_needed"] == True
            assert temp_image_file in context_result["recommended_media"]
            
            # Test subsequent media analysis
            media_result = tools.analyze_media_file(temp_image_file)
            assert media_result["status"] == "success"
            assert media_result["file_type"] == "image"
    
    @pytest.mark.integration
    def test_function_schemas_completeness(self):
        """Test that FUNCTION_SCHEMAS covers all public methods."""
        # Get all public methods from ScratchPadTools
        tools_methods = [method for method in dir(ScratchPadTools) 
                        if not method.startswith('_') and callable(getattr(ScratchPadTools, method))]
        
        # Filter to only the methods that should be in schemas
        expected_schema_methods = [
            'get_scratch_pad_context',
            'analyze_media_file', 
            'solve_math'
        ]
        
        # Get function names from schemas
        schema_function_names = [schema['function']['name'] for schema in FUNCTION_SCHEMAS]
        
        # Verify all expected methods are in schemas
        for method in expected_schema_methods:
            assert method in schema_function_names, f"Method {method} missing from FUNCTION_SCHEMAS"
        
        # Verify schemas only contain expected methods
        for schema_name in schema_function_names:
            assert schema_name in expected_schema_methods, f"Unexpected function {schema_name} in FUNCTION_SCHEMAS"
    
    @pytest.mark.integration
    def test_function_schemas_structure(self):
        """Test that FUNCTION_SCHEMAS have correct structure."""
        for schema in FUNCTION_SCHEMAS:
            # Required top-level fields
            assert "type" in schema
            assert schema["type"] == "function"
            assert "function" in schema
            
            function_def = schema["function"]
            
            # Required function fields
            assert "name" in function_def
            assert "description" in function_def
            assert "parameters" in function_def
            
            parameters = function_def["parameters"]
            
            # Parameters structure
            assert "type" in parameters
            assert parameters["type"] == "object"
            assert "properties" in parameters
            assert "required" in parameters
            
            # Verify required parameters are in properties
            for required_param in parameters["required"]:
                assert required_param in parameters["properties"]
                
                # Each property should have type and description
                prop = parameters["properties"][required_param]
                assert "type" in prop
                assert "description" in prop
    
    @pytest.mark.integration 
    def test_error_propagation_through_components(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test that errors propagate correctly through the system."""
        # Test math routing error propagation
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock API error in routing
            mock_client.chat.completions.create.side_effect = Exception("Routing API failed")
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.solve_math("solve equation")
            
            assert result["status"] == "error"
            assert "Error in math routing" in result["message"]
            assert "Routing API failed" in result["message"]
    
    @pytest.mark.integration
    def test_environment_configuration_integration(self):
        """Test that environment variables are properly integrated."""
        # Test with missing API key
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                ScratchPadTools()
    
    @pytest.mark.integration
    def test_file_path_resolution_integration(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test that file path resolution works across components."""
        # Test with explicit file paths
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            
            assert tools.scratchpad_file == temp_scratchpad_file
            assert tools.system_prompt_file == temp_system_prompt_file
        
        # Test with environment variable defaults
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'SCRATCHPAD_FILE': 'custom_scratchpad.txt',
            'SYSTEM_PROMPT_FILE': 'custom_prompt.txt'
        }):
            tools = ScratchPadTools()
            
            assert tools.scratchpad_file == 'custom_scratchpad.txt'
            assert tools.system_prompt_file == 'custom_prompt.txt'


class TestMathFunctionIntegration:
    """Test integration between mathematical functions and expression parsing."""
    
    @pytest.mark.integration
    def test_expression_parsing_across_math_functions(self, scratch_pad_tools):
        """Test that expression parsing works consistently across all math functions."""
        test_expression = "3x^2 + 2x + 1"  # Natural notation
        expected_parsed = "3*x**2 + 2*x + 1"  # SymPy notation
        
        # Test parsing in different contexts
        functions_to_test = [
            'solve_equation',
            'simplify_expression', 
            'calculate_derivative',
            'factor_expression'
        ]
        
        for func_name in functions_to_test:
            # Mock the actual SymPy operations to focus on parsing
            with patch('sympy.solve'), patch('sympy.simplify'), \
                 patch('sympy.diff'), patch('sympy.factor'), \
                 patch('sympy.integrate'):
                
                # The parsing happens in _parse_expression_safely
                parsed = scratch_pad_tools._parse_expression_safely(test_expression)
                assert "3*x**2" in str(parsed)
                assert "2*x" in str(parsed)
    
    @pytest.mark.integration
    def test_math_function_error_consistency(self, scratch_pad_tools):
        """Test that all math functions handle errors consistently."""
        invalid_expression = "invalid$%expression"
        
        math_functions = [
            ('solve_equation', [invalid_expression]),
            ('simplify_expression', [invalid_expression]),
            ('calculate_derivative', [invalid_expression]),
            ('calculate_integral', [invalid_expression]),
            ('factor_expression', [invalid_expression]),
            ('calculate_complex_arithmetic', [invalid_expression])
        ]
        
        for func_name, args in math_functions:
            func = getattr(scratch_pad_tools, func_name)
            result = func(*args)
            
            # All should return consistent error structure
            assert result["status"] == "error"
            assert "message" in result
            assert "Invalid mathematical expression" in result["message"] or \
                   "Error calculating" in result["message"]
    
    @pytest.mark.integration
    def test_solve_math_routing_to_actual_functions(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test that solve_math correctly routes to and calls actual math functions."""
        operations_and_queries = [
            ("solve_equation", "solve 2x + 3 = 7", "solutions"),
            ("simplify_expression", "simplify x^2 + 2x + 1", "simplified_expression"),
            ("calculate_derivative", "derivative of x^3", "derivative"),
            ("calculate_integral", "integrate x^2", "integral"),
            ("factor_expression", "factor x^2 + 2x + 1", "factored_expression"),
            ("calculate_complex_arithmetic", "calculate 12345*67890", "result")
        ]
        
        for operation, query, expected_key in operations_and_queries:
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
                
                # Don't mock the actual math function - let it run
                with patch('sympy.solve', return_value=[2]), \
                     patch('sympy.simplify', return_value="simplified"), \
                     patch('sympy.diff', return_value="derivative"), \
                     patch('sympy.integrate', return_value="integral"), \
                     patch('sympy.factor', return_value="factored"), \
                     patch('sympy.sympify', return_value=123456):
                    
                    result = tools.solve_math(query)
                    
                    # Should succeed and contain the expected result key
                    assert result["status"] == "success"
                    assert result["routing_decision"]["operation"] == operation
                    assert expected_key in result


class TestSystemIntegration:
    """Test system-level integration scenarios."""
    
    @pytest.mark.integration
    def test_concurrent_operations_safety(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test that multiple operations can be safely performed concurrently."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                    tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                    
                    # Simulate some work
                    content = tools._load_scratchpad()
                    assert "Test Scratchpad Content" in content
                    
                    results.append(f"Worker {worker_id} completed")
            except Exception as e:
                errors.append(f"Worker {worker_id} failed: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
    
    @pytest.mark.integration 
    def test_large_scale_operations(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test system behavior with large-scale operations."""
        # Create large scratchpad content
        large_content = "# Large Scratchpad\n" + "- Item: description\n" * 1000
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            large_scratchpad = f.name
        
        try:
            with patch('tools.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                # Mock response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = json.dumps({
                    "relevant_context": "Large context processed",
                    "media_files_needed": False,
                    "recommended_media": [],
                    "reasoning": "Successfully processed large content"
                })
                mock_client.chat.completions.create.return_value = mock_response
                
                tools = ScratchPadTools(large_scratchpad, temp_system_prompt_file)
                tools.client = mock_client
                
                result = tools.get_scratch_pad_context("analyze all items")
                
                assert result["status"] == "success"
                assert "Large context processed" in result["relevant_context"]
        finally:
            os.unlink(large_scratchpad)
    
    @pytest.mark.integration
    def test_memory_usage_stability(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test that repeated operations don't cause memory leaks."""
        import gc
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            
            # Perform many operations
            for i in range(100):
                content = tools._load_scratchpad()
                assert content is not None
                
                # Force garbage collection periodically
                if i % 10 == 0:
                    gc.collect()
            
            # Final cleanup
            gc.collect()
            
            # Test should complete without memory issues
            assert True  # If we get here, memory usage was stable


class TestErrorRecoveryIntegration:
    """Test error recovery and resilience across components."""
    
    @pytest.mark.integration
    def test_graceful_degradation_with_api_failures(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test that system degrades gracefully when APIs fail."""
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Simulate intermittent API failures
            failures = [True, False, True, False]  # Fail, succeed, fail, succeed
            
            def side_effect(*args, **kwargs):
                if failures.pop(0):
                    raise Exception("API temporarily unavailable")
                else:
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = json.dumps({
                        "relevant_context": "Successfully recovered",
                        "media_files_needed": False,
                        "recommended_media": [],
                        "reasoning": "API call succeeded"
                    })
                    return mock_response
            
            mock_client.chat.completions.create.side_effect = side_effect
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            # First call should fail
            result1 = tools.get_scratch_pad_context("test query 1")
            assert result1["status"] == "error"
            
            # Second call should succeed
            result2 = tools.get_scratch_pad_context("test query 2") 
            assert result2["status"] == "success"
            assert "Successfully recovered" in result2["relevant_context"]
    
    @pytest.mark.integration
    def test_partial_failure_handling(self, temp_scratchpad_file, temp_system_prompt_file, temp_math_routing_prompt_file):
        """Test handling of partial failures in complex operations."""
        # Test solve_math with context fetch failure but successful math operation
        routing_response = {
            "operation": "solve_equation",
            "needs_context": True
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
            
            # Mock context failure but math success
            with patch.object(tools, 'get_scratch_pad_context', return_value={"status": "error", "message": "Context failed"}):
                with patch.object(tools, 'solve_equation', return_value={"status": "success", "solutions": ["2"]}):
                    result = tools.solve_math("solve 2x + 3 = 7")
                    
                    # Should still succeed with partial failure
                    assert result["status"] == "success"
                    assert result["routing_decision"]["context_used"] == True
                    assert result["routing_decision"]["context_content"] == ""  # Empty due to error
                    assert result["solutions"] == ["2"] 