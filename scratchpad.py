#!/usr/bin/env python3
"""
Scratch Pad AI Tool

A personal knowledge assistant that processes queries by loading and analyzing
a local scratch pad document to provide relevant contextual responses.

Usage: scratchpad "What are my current AI projects?"
"""

import os
import sys
import click
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path


class ScratchPadTool:
    """Main Scratch Pad AI tool for intelligent context extraction."""
    
    def __init__(self, scratchpad_file: str = None, system_prompt_file: str = None):
        """Initialize the Scratch Pad tool.
        
        Args:
            scratchpad_file: Path to scratch pad file (defaults to SCRATCHPAD_FILE env var)
            system_prompt_file: Path to system prompt file (defaults to SYSTEM_PROMPT_FILE env var)
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        
        # Set file paths (parameterized for multi-user support)
        self.scratchpad_file = scratchpad_file or os.getenv('SCRATCHPAD_FILE', 'scratchpad.txt')
        self.system_prompt_file = system_prompt_file or os.getenv('SYSTEM_PROMPT_FILE', 'config/system_prompt.txt')
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from file."""
        try:
            with open(self.system_prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            # Fallback system prompt if file not found
            return ("You are a personal knowledge assistant. Extract and return the most "
                   "relevant context from the scratch pad to help answer the user's question.")
    
    def _load_scratchpad(self) -> str:
        """Load the scratch pad content from file."""
        try:
            with open(self.scratchpad_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Scratch pad file not found: {self.scratchpad_file}")
    
    def _determine_media_necessity(self, query: str, scratchpad_content: str) -> dict:
        """
        Stage 1: Determine if media files are necessary and if visual analysis is needed.
        
        Returns:
            dict: {
                'media_necessary': bool,
                'visual_analysis_needed': bool,
                'relevant_media_files': list,
                'reasoning': str
            }
        """
        assessment_prompt = f"""
        Given this user query and scratch pad content, determine:
        1. Are any media files mentioned in the scratch pad necessary to answer this query?
        2. If media is relevant, is the existing text summary sufficient or is detailed visual analysis needed?

        USER QUERY: {query}

        SCRATCH PAD CONTENT:
        {scratchpad_content}

        Respond in this exact format:
        MEDIA_NECESSARY: [yes/no]
        VISUAL_ANALYSIS_NEEDED: [yes/no]
        RELEVANT_FILES: [comma-separated list of file paths, or "none"]
        REASONING: [brief explanation]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a media assessment specialist. Analyze queries to determine media processing needs."},
                    {"role": "user", "content": assessment_prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Parse the structured response
            result = {
                'media_necessary': False,
                'visual_analysis_needed': False,
                'relevant_media_files': [],
                'reasoning': ''
            }
            
            for line in content.split('\n'):
                if line.startswith('MEDIA_NECESSARY:'):
                    result['media_necessary'] = 'yes' in line.lower()
                elif line.startswith('VISUAL_ANALYSIS_NEEDED:'):
                    result['visual_analysis_needed'] = 'yes' in line.lower()
                elif line.startswith('RELEVANT_FILES:'):
                    files = line.split(':', 1)[1].strip()
                    if files.lower() != 'none':
                        result['relevant_media_files'] = [f.strip() for f in files.split(',')]
                elif line.startswith('REASONING:'):
                    result['reasoning'] = line.split(':', 1)[1].strip()
            
            return result
            
        except Exception as e:
            print(f"Error in media assessment: {e}")
            return {
                'media_necessary': False,
                'visual_analysis_needed': False,
                'relevant_media_files': [],
                'reasoning': 'Assessment failed - proceeding with text-only analysis'
            }
    
    def _process_query_with_context(self, query: str, scratchpad_content: str, media_assessment: dict = None) -> str:
        """
        Stage 2: Process the query with full context extraction.
        
        Args:
            query: User's question
            scratchpad_content: Full scratch pad content
            media_assessment: Results from media necessity assessment
            
        Returns:
            str: Formatted response with relevant context
        """
        # Prepare the prompt with media assessment info
        media_info = ""
        if media_assessment:
            media_info = f"""
MEDIA ASSESSMENT:
- Media files necessary: {media_assessment.get('media_necessary', False)}
- Visual analysis needed: {media_assessment.get('visual_analysis_needed', False)}
- Relevant files: {media_assessment.get('relevant_media_files', [])}
- Assessment reasoning: {media_assessment.get('reasoning', 'N/A')}
"""
        
        full_prompt = f"""
        {media_info}
        
        USER QUERY: {query}
        
        SCRATCH PAD CONTENT:
        {scratchpad_content}
        
        Extract and provide the most relevant context to answer the user's query.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error processing query: {e}"
    
    def process_query(self, query: str) -> str:
        """
        Main method to process a user query using the two-stage approach.
        
        Args:
            query: User's question
            
        Returns:
            str: Formatted response with relevant context
        """
        # Load scratch pad content
        try:
            scratchpad_content = self._load_scratchpad()
        except FileNotFoundError as e:
            return f"**Error:** {e}"
        
        # Stage 1: Assess media necessity
        media_assessment = self._determine_media_necessity(query, scratchpad_content)
        
        # Stage 2: Process query with context
        response = self._process_query_with_context(query, scratchpad_content, media_assessment)
        
        return response


@click.command()
@click.argument('query', required=True)
@click.option('--scratchpad-file', '-f', help='Path to scratch pad file')
@click.option('--system-prompt-file', '-p', help='Path to system prompt file')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed processing information')
def main(query: str, scratchpad_file: str, system_prompt_file: str, verbose: bool):
    """
    Scratch Pad AI Tool
    
    Process queries using your personal scratch pad document for intelligent context extraction.
    
    Examples:
        scratchpad "What are my current AI projects?"
        scratchpad "What's my date of birth?"
        scratchpad "Show me information about the gorilla artwork"
    """
    try:
        # Initialize the tool
        tool = ScratchPadTool(scratchpad_file, system_prompt_file)
        
        if verbose:
            print(f"📁 Using scratch pad: {tool.scratchpad_file}")
            print(f"⚙️  Using system prompt: {tool.system_prompt_file}")
            print(f"❓ Query: {query}\n")
        
        # Process the query
        result = tool.process_query(query)
        
        # Display the result
        print(result)
        
    except Exception as e:
        print(f"**Error:** {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main() 