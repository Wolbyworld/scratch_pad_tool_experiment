#!/usr/bin/env python3
"""
Unit tests for scratchpad context extraction in ScratchPadTools.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from tools import ScratchPadTools


class TestScratchPadContext:
    """Test scratchpad context extraction functionality."""
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_success(self, temp_scratchpad_file, temp_system_prompt_file, mock_openai_client):
        """Test successful context extraction."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_openai_client
            
            result = tools.get_scratch_pad_context("Tell me about my current projects")
            
            assert result["status"] == "success"
            assert result["query"] == "Tell me about my current projects"
            assert "relevant_context" in result
            assert "media_files_needed" in result
            assert "recommended_media" in result
            assert "reasoning" in result
            
            # Verify OpenAI client was called
            mock_openai_client.responses.create.assert_called_once()
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_file_not_found(self, temp_system_prompt_file):
        """Test handling of missing scratchpad file."""
        nonexistent_file = "/nonexistent/scratchpad.txt"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(nonexistent_file, temp_system_prompt_file)
            
            result = tools.get_scratch_pad_context("test query")
            
            assert result["status"] == "error"
            assert f"Scratch pad file not found: {nonexistent_file}" in result["message"]
            assert result["relevant_context"] == ""
            assert result["media_files_needed"] == False
            assert result["recommended_media"] == []
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_with_media_recommendation(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test context extraction that recommends media files."""
        mock_response_with_media = {
            "relevant_context": "User has gorilla image in media folder",
            "media_files_needed": True,
            "recommended_media": ["media/gorilla.png", "media/test_image.png"],
            "reasoning": "Images would help explain the visual content"
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            mock_response.output_text = json.dumps(mock_response_with_media)
            mock_response.output = []
            mock_client.responses.create.return_value = mock_response
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.get_scratch_pad_context("Show me the gorilla image")
            
            assert result["status"] == "success"
            assert result["media_files_needed"] == True
            assert "media/gorilla.png" in result["recommended_media"]
            assert result["reasoning"] == "Images would help explain the visual content"
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_invalid_json_response(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of invalid JSON response from OpenAI."""
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            # Invalid JSON response
            mock_response.output_text = "This is not valid JSON"
            mock_response.output = []
            mock_client.responses.create.return_value = mock_response
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.get_scratch_pad_context("test query")
            
            assert result["status"] == "success"  # Should fallback gracefully
            assert result["relevant_context"] == "This is not valid JSON"
            assert result["media_files_needed"] == False
            assert result["reasoning"] == "JSON parsing failed, using raw response"
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_partial_json_response(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of partial/incomplete JSON response."""
        partial_json = {
            "relevant_context": "Some context",
            # Missing other required fields
        }
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            mock_response.output_text = json.dumps(partial_json)
            mock_response.output = []
            mock_client.responses.create.return_value = mock_response
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.get_scratch_pad_context("test query")
            
            assert result["status"] == "success"
            assert result["relevant_context"] == "Some context"
            # Should provide defaults for missing fields
            assert result["media_files_needed"] == False
            assert result["recommended_media"] == []
            assert result["reasoning"] == ""
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_json_wrapped_in_markdown(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of JSON wrapped in markdown code blocks."""
        json_content = {
            "relevant_context": "Context from markdown",
            "media_files_needed": False,
            "recommended_media": [],
            "reasoning": "No media needed"
        }
        
        markdown_wrapped_response = f"""```json
{json.dumps(json_content)}
```"""
        
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            mock_response.output_text = markdown_wrapped_response
            mock_response.output = []
            mock_client.responses.create.return_value = mock_response
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.get_scratch_pad_context("test query")
            
            assert result["status"] == "success"
            assert result["relevant_context"] == "Context from markdown"
            assert result["media_files_needed"] == False
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_openai_api_error(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of OpenAI API errors."""
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock API error
            mock_client.responses.create.side_effect = Exception("API rate limit exceeded")
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.get_scratch_pad_context("test query")
            
            assert result["status"] == "error"
            assert "API rate limit exceeded" in result["message"]
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_empty_scratchpad(self, temp_system_prompt_file, mock_openai_client):
        """Test handling of empty scratchpad file."""
        # Create empty scratchpad file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")  # Empty content
            empty_scratchpad = f.name
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(empty_scratchpad, temp_system_prompt_file)
                tools.client = mock_openai_client
                
                result = tools.get_scratch_pad_context("test query")
                
                assert result["status"] == "success"
                # Should still work with empty content
                assert "relevant_context" in result
        finally:
            os.unlink(empty_scratchpad)
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_large_content(self, temp_system_prompt_file, mock_openai_client):
        """Test handling of very large scratchpad content."""
        # Create large scratchpad content
        large_content = "# Large Content\n" + "This is a test line.\n" * 1000
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            large_scratchpad = f.name
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(large_scratchpad, temp_system_prompt_file)
                tools.client = mock_openai_client
                
                result = tools.get_scratch_pad_context("test query")
                
                assert result["status"] == "success"
                # Verify the large content was passed to OpenAI
                call_args = mock_openai_client.responses.create.call_args
                user_message = call_args[1]["input"][1]["content"]
                assert "This is a test line." in user_message
        finally:
            os.unlink(large_scratchpad)
    
    @pytest.mark.unit
    def test_get_scratch_pad_context_system_prompt_not_found(self, temp_scratchpad_file):
        """Test handling of missing system prompt file."""
        nonexistent_prompt = "/nonexistent/system_prompt.txt"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('tools.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                # Should use fallback system prompt
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = json.dumps({
                    "relevant_context": "Fallback context",
                    "media_files_needed": False,
                    "recommended_media": [],
                    "reasoning": "Using fallback"
                })
                mock_response.output_text = json.dumps({
                    "relevant_context": "test context",
                    "media_files_needed": False,
                    "recommended_media": [],
                    "reasoning": "Using fallback"
                })
                mock_response.output = []
                mock_client.responses.create.return_value = mock_response
                
                tools = ScratchPadTools(temp_scratchpad_file, nonexistent_prompt)
                tools.client = mock_client
                
                result = tools.get_scratch_pad_context("test query")
                
                # Should still work with fallback system prompt
                assert result["status"] == "success"
                
                # Verify fallback system prompt was used
                call_args = mock_client.responses.create.call_args
                system_message = call_args[1]["input"][0]["content"]
                assert "context extraction specialist" in system_message


class TestScratchPadHelperMethods:
    """Test helper methods for scratchpad functionality."""
    
    @pytest.mark.unit
    def test_load_scratchpad_success(self, temp_scratchpad_file):
        """Test successful scratchpad loading."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, "dummy_prompt.txt")
            
            content = tools._load_scratchpad()
            
            assert "Test Scratchpad Content" in content
            assert "Test User" in content
            assert "Math calculator integration" in content
    
    @pytest.mark.unit
    def test_load_scratchpad_file_not_found(self):
        """Test scratchpad loading with missing file."""
        nonexistent = "/nonexistent/file.txt"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(nonexistent, "dummy_prompt.txt")
            
            content = tools._load_scratchpad()
            
            assert content.startswith("Error:")
            assert nonexistent in content
    
    @pytest.mark.unit
    def test_load_system_prompt_success(self, temp_system_prompt_file):
        """Test successful system prompt loading."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools("dummy_scratchpad.txt", temp_system_prompt_file)
            
            prompt = tools._load_system_prompt()
            
            assert "test system prompt" in prompt
            assert "JSON format" in prompt
    
    @pytest.mark.unit
    def test_load_system_prompt_file_not_found(self):
        """Test system prompt loading with missing file."""
        nonexistent = "/nonexistent/prompt.txt"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools("dummy_scratchpad.txt", nonexistent)
            
            prompt = tools._load_system_prompt()
            
            # Should return fallback prompt
            assert "context extraction specialist" in prompt
            assert "Return valid JSON only" in prompt


class TestScratchPadEdgeCases:
    """Test edge cases and error conditions for scratchpad functionality."""
    
    @pytest.mark.unit
    def test_unicode_content_handling(self, temp_system_prompt_file, mock_openai_client):
        """Test handling of Unicode characters in scratchpad content."""
        unicode_content = """# Unicode Test Content
        
        - Name: José María
        - Notes: Testing with émojis 🚀 and special chars: áéíóú
        - Math: ∫∆√π∞
        """
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(unicode_content)
            unicode_scratchpad = f.name
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(unicode_scratchpad, temp_system_prompt_file)
                tools.client = mock_openai_client
                
                result = tools.get_scratch_pad_context("Tell me about José")
                
                assert result["status"] == "success"
                # Should handle Unicode properly
                call_args = mock_openai_client.responses.create.call_args
                user_message = call_args[1]["input"][1]["content"]
                assert "José María" in user_message
                assert "🚀" in user_message
        finally:
            os.unlink(unicode_scratchpad)
    
    @pytest.mark.unit
    def test_very_long_query(self, temp_scratchpad_file, temp_system_prompt_file, mock_openai_client):
        """Test handling of very long queries."""
        very_long_query = "Tell me about " + "my projects " * 500  # Very long query
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_openai_client
            
            result = tools.get_scratch_pad_context(very_long_query)
            
            assert result["status"] == "success"
            assert result["query"] == very_long_query
    
    @pytest.mark.unit
    def test_special_characters_in_query(self, temp_scratchpad_file, temp_system_prompt_file, mock_openai_client):
        """Test handling of special characters in queries."""
        special_query = "What about @#$%^&*(){}[]|\\:;\"'<>?/`~"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_openai_client
            
            result = tools.get_scratch_pad_context(special_query)
            
            assert result["status"] == "success"
            assert result["query"] == special_query 