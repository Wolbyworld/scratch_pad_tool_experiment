#!/usr/bin/env python3
"""
Unit tests for media analysis functionality in ScratchPadTools.
"""

import pytest
import os
import base64
import tempfile
from unittest.mock import Mock, patch, mock_open
from tools import ScratchPadTools


class TestMediaAnalysis:
    """Test media file analysis functionality."""
    
    @pytest.mark.unit
    def test_analyze_media_file_image_success(self, temp_image_file, temp_scratchpad_file, temp_system_prompt_file):
        """Test successful image analysis."""
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock successful vision API response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "This is a test image showing a 1x1 pixel PNG file."
            mock_client.chat.completions.create.return_value = mock_response
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.analyze_media_file(temp_image_file)
            
            assert result["status"] == "success"
            assert result["file_path"] == temp_image_file
            assert result["file_type"] == "image"
            assert result["analysis"] == "This is a test image showing a 1x1 pixel PNG file."
            assert result["mime_type"] == "image/png"
            
            # Verify vision API was called with correct parameters
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-4o-mini"
            
            # Check that the image was included in the request
            messages = call_args[1]["messages"]
            assert len(messages) == 1
            assert messages[0]["role"] == "user"
            content = messages[0]["content"]
            assert len(content) == 2  # Text and image
            assert content[0]["type"] == "text"
            assert content[1]["type"] == "image_url"
            assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    
    @pytest.mark.unit
    def test_analyze_media_file_not_found(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of missing media file."""
        nonexistent_file = "/nonexistent/image.png"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            
            result = tools.analyze_media_file(nonexistent_file)
            
            assert result["status"] == "error"
            assert f"Media file not found: {nonexistent_file}" in result["message"]
            assert result["analysis"] == ""
            assert result["file_type"] == "unknown"
    
    @pytest.mark.unit
    def test_analyze_media_file_pdf(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of PDF files."""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\ntest pdf content')
            pdf_file = f.name
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                
                result = tools.analyze_media_file(pdf_file)
                
                assert result["status"] == "success"
                assert result["file_path"] == pdf_file
                assert result["file_type"] == "pdf"
                assert "PDF file detected" in result["analysis"]
                assert "not yet implemented for PDFs" in result["analysis"]
                assert "text summary from the scratch pad" in result["recommendation"]
        finally:
            os.unlink(pdf_file)
    
    @pytest.mark.unit
    def test_analyze_media_file_unsupported_type(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of unsupported file types."""
        # Create temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'unsupported file content')
            unsupported_file = f.name
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                
                result = tools.analyze_media_file(unsupported_file)
                
                assert result["status"] == "error"
                assert "Unsupported file type: .xyz" in result["message"]
                assert result["analysis"] == ""
                assert result["file_type"] == ".xyz"
        finally:
            os.unlink(unsupported_file)
    
    @pytest.mark.unit
    def test_analyze_media_file_different_image_formats(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of different image formats."""
        formats_and_mimes = [
            ('.jpg', 'image/jpeg'),
            ('.jpeg', 'image/jpeg'),
            ('.gif', 'image/gif'),
            ('.webp', 'image/webp')
        ]
        
        # Simple 1x1 PNG data (we'll pretend it's different formats)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        for ext, expected_mime in formats_and_mimes:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(png_data)
                test_file = f.name
            
            try:
                with patch('tools.OpenAI') as mock_openai:
                    mock_client = Mock()
                    mock_openai.return_value = mock_client
                    
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = f"Analysis of {ext} image"
                    mock_client.chat.completions.create.return_value = mock_response
                    
                    tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                    tools.client = mock_client
                    
                    result = tools.analyze_media_file(test_file)
                    
                    assert result["status"] == "success"
                    assert result["file_type"] == "image"
                    assert result["mime_type"] == expected_mime
                    
                    # Verify correct MIME type in API call
                    call_args = mock_client.chat.completions.create.call_args
                    image_url = call_args[1]["messages"][0]["content"][1]["image_url"]["url"]
                    assert image_url.startswith(f"data:{expected_mime};base64,")
            finally:
                os.unlink(test_file)
    
    @pytest.mark.unit
    def test_analyze_media_file_openai_api_error(self, temp_image_file, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of OpenAI API errors during image analysis."""
        with patch('tools.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock API error
            mock_client.chat.completions.create.side_effect = Exception("Vision API rate limit exceeded")
            
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            tools.client = mock_client
            
            result = tools.analyze_media_file(temp_image_file)
            
            assert result["status"] == "error"
            assert "Vision API rate limit exceeded" in result["message"]
            assert result["analysis"] == ""
            assert result["file_type"] == "image"
    
    @pytest.mark.unit
    def test_analyze_media_file_general_exception(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of general exceptions during media analysis."""
        # Create a file that exists but will cause an error during processing
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'invalid image data')
            invalid_image = f.name
        
        try:
            with patch('tools.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                # Mock the _encode_image method to raise an exception
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                tools.client = mock_client
                
                with patch.object(tools, '_encode_image', side_effect=Exception("Image encoding failed")):
                    result = tools.analyze_media_file(invalid_image)
                    
                    assert result["status"] == "error"
                    assert "Error analyzing media file" in result["message"]
                    assert "Image encoding failed" in result["message"]
                    assert result["analysis"] == ""
                    assert result["file_type"] == "unknown"
        finally:
            os.unlink(invalid_image)


class TestImageEncoding:
    """Test image encoding functionality."""
    
    @pytest.mark.unit
    def test_encode_image_success(self, temp_image_file, temp_scratchpad_file, temp_system_prompt_file):
        """Test successful image encoding to base64."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            
            encoded = tools._encode_image(temp_image_file)
            
            # Should not start with "Error"
            assert not encoded.startswith("Error")
            
            # Should be valid base64
            try:
                decoded = base64.b64decode(encoded)
                assert len(decoded) > 0
            except Exception:
                pytest.fail("Encoded result is not valid base64")
    
    @pytest.mark.unit
    def test_encode_image_file_not_found(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test image encoding with missing file."""
        nonexistent_file = "/nonexistent/image.png"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
            
            result = tools._encode_image(nonexistent_file)
            
            assert result.startswith("Error encoding image:")
    
    @pytest.mark.unit
    def test_encode_image_permission_error(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test image encoding with permission error."""
        # Create a file and then make it unreadable
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'test data')
            restricted_file = f.name
        
        try:
            # Make file unreadable
            os.chmod(restricted_file, 0o000)
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                
                result = tools._encode_image(restricted_file)
                
                assert result.startswith("Error encoding image:")
        finally:
            # Restore permissions and cleanup
            os.chmod(restricted_file, 0o644)
            os.unlink(restricted_file)
    
    @pytest.mark.unit
    def test_encode_image_empty_file(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test image encoding with empty file."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            # Empty file
            empty_file = f.name
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                
                encoded = tools._encode_image(empty_file)
                
                # Should succeed with empty file (base64 of empty bytes)
                assert not encoded.startswith("Error")
                assert encoded == ""  # base64 of empty bytes
        finally:
            os.unlink(empty_file)
    
    @pytest.mark.unit
    def test_encode_image_large_file(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test image encoding with large file."""
        # Create a larger test file
        large_data = b'large image data content ' * 1000
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(large_data)
            large_file = f.name
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                
                encoded = tools._encode_image(large_file)
                
                assert not encoded.startswith("Error")
                
                # Verify it's valid base64 and decodes to original data
                decoded = base64.b64decode(encoded)
                assert decoded == large_data
        finally:
            os.unlink(large_file)


class TestMediaAnalysisEdgeCases:
    """Test edge cases and boundary conditions for media analysis."""
    
    @pytest.mark.unit
    def test_analyze_media_file_unicode_filename(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of files with Unicode characters in filename."""
        unicode_filename = "测试图片_émoji🖼️.png"
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Create file with Unicode name in temp directory
        import tempfile
        temp_dir = tempfile.mkdtemp()
        unicode_file = os.path.join(temp_dir, unicode_filename)
        
        try:
            with open(unicode_file, 'wb') as f:
                f.write(png_data)
            
            with patch('tools.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Unicode filename image analysis"
                mock_client.chat.completions.create.return_value = mock_response
                
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                tools.client = mock_client
                
                result = tools.analyze_media_file(unicode_file)
                
                assert result["status"] == "success"
                assert result["file_path"] == unicode_file
                assert unicode_filename in result["file_path"]
        finally:
            if os.path.exists(unicode_file):
                os.unlink(unicode_file)
            os.rmdir(temp_dir)
    
    @pytest.mark.unit
    def test_analyze_media_file_very_long_path(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of files with very long paths."""
        # Create nested directory structure
        import tempfile
        base_temp = tempfile.mkdtemp()
        
        # Create deep nested structure
        long_path_parts = ["very", "long", "path", "structure"] * 10
        current_path = base_temp
        for part in long_path_parts:
            current_path = os.path.join(current_path, part)
            os.makedirs(current_path, exist_ok=True)
        
        long_file = os.path.join(current_path, "test.png")
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        try:
            with open(long_file, 'wb') as f:
                f.write(png_data)
            
            with patch('tools.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Long path image analysis"
                mock_client.chat.completions.create.return_value = mock_response
                
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                tools.client = mock_client
                
                result = tools.analyze_media_file(long_file)
                
                assert result["status"] == "success"
                assert result["file_path"] == long_file
        finally:
            # Cleanup deep directory structure
            import shutil
            shutil.rmtree(base_temp, ignore_errors=True)
    
    @pytest.mark.unit
    def test_analyze_media_file_case_insensitive_extensions(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of case-insensitive file extensions."""
        case_variations = ['.PNG', '.Jpg', '.JPEG', '.GiF', '.WebP']
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        for ext in case_variations:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(png_data)
                test_file = f.name
            
            try:
                with patch('tools.OpenAI') as mock_openai:
                    mock_client = Mock()
                    mock_openai.return_value = mock_client
                    
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = f"Analysis of {ext} file"
                    mock_client.chat.completions.create.return_value = mock_response
                    
                    tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                    tools.client = mock_client
                    
                    result = tools.analyze_media_file(test_file)
                    
                    # Should be recognized as image regardless of case
                    assert result["status"] == "success"
                    assert result["file_type"] == "image"
            finally:
                os.unlink(test_file)
    
    @pytest.mark.unit
    def test_analyze_media_file_with_no_extension(self, temp_scratchpad_file, temp_system_prompt_file):
        """Test handling of files with no extension."""
        with tempfile.NamedTemporaryFile(suffix='', delete=False) as f:
            f.write(b'some file content')
            no_ext_file = f.name
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                tools = ScratchPadTools(temp_scratchpad_file, temp_system_prompt_file)
                
                result = tools.analyze_media_file(no_ext_file)
                
                # Should be treated as unsupported type
                assert result["status"] == "error"
                assert "Unsupported file type:" in result["message"]
        finally:
            os.unlink(no_ext_file) 