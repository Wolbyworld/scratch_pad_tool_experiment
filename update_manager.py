#!/usr/bin/env python3
"""
Scratchpad Update Manager

Analyzes conversations to determine if the scratchpad should be updated with new
information, corrections, or improvements. Runs automatically after each user-AI cycle.

Usage: Called programmatically from luzia.py
"""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import colorama
from colorama import Fore, Style


class ScratchpadUpdateManager:
    """Manages intelligent scratchpad updates based on conversation analysis."""
    
    def __init__(self, scratchpad_file: str = None, update_prompt_file: str = None, no_update_file: str = None):
        """Initialize the Update Manager.
        
        Args:
            scratchpad_file: Path to scratch pad file
            update_prompt_file: Path to update analysis system prompt
            no_update_file: Path to PII restrictions file
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
        self.update_prompt_file = update_prompt_file or 'config/update_analysis_prompt.txt'
        self.no_update_file = no_update_file or 'config/no_update.txt'
        
        # Load configuration files
        self.update_prompt = self._load_update_prompt()
        self.no_update_restrictions = self._load_no_update_restrictions()
        
        # Initialize colorama for colored logging
        colorama.init()
    
    def _load_update_prompt(self) -> str:
        """Load the update analysis system prompt from file."""
        try:
            with open(self.update_prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Update prompt file not found: {self.update_prompt_file}")
        except Exception as e:
            raise Exception(f"Error loading update prompt: {e}")
    
    def _load_no_update_restrictions(self) -> str:
        """Load the PII and content restrictions from file."""
        try:
            with open(self.no_update_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"No-update restrictions file not found: {self.no_update_file}")
        except Exception as e:
            raise Exception(f"Error loading no-update restrictions: {e}")
    
    def _load_current_scratchpad(self) -> str:
        """Load current scratchpad content."""
        try:
            with open(self.scratchpad_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "# MY SCRATCH PAD\n\n## MEDIA DOCUMENTS\n\n## USER FACTS"
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Failed to load scratchpad: {e}{Style.RESET_ALL}")
            return ""
    
    def _log_update_analysis(self, message: str, color: str = Fore.CYAN):
        """Log update analysis messages with color."""
        print(f"{color}[UPDATE] {message}{Style.RESET_ALL}")
    
    def analyze_conversation_for_updates(
        self, 
        user_message: str,
        ai_response: str, 
        function_calls: List[Dict] = None,
        tool_responses: List[Dict] = None
    ) -> Dict:
        """Analyze a conversation cycle for potential scratchpad updates.
        
        Args:
            user_message: The user's last message
            ai_response: Luzia's response
            function_calls: List of function calls made (get_scratch_pad_context, analyze_media_file)
            tool_responses: List of responses from function calls
            
        Returns:
            Dictionary with analysis results and any proposed updates
        """
        self._log_update_analysis("Analyzing conversation for scratchpad updates...")
        
        try:
            # Get current scratchpad content
            current_scratchpad = self._load_current_scratchpad()
            
            # Prepare conversation context
            conversation_context = self._prepare_conversation_context(
                user_message, ai_response, function_calls, tool_responses
            )
            
            # Analyze with GPT-4.1-nano
            analysis_result = self._analyze_with_ai(conversation_context, current_scratchpad)
            
            if analysis_result.get('should_update', False):
                self._log_update_analysis(
                    f"Update recommended: {analysis_result.get('reasoning', 'No reason provided')}", 
                    Fore.YELLOW
                )
                return analysis_result
            else:
                self._log_update_analysis("No updates needed", Fore.GREEN)
                return analysis_result
                
        except Exception as e:
            self._log_update_analysis(f"Analysis failed: {e}", Fore.RED)
            # KISS: Return no updates on error
            return {"should_update": False, "error": str(e)}
    
    def _prepare_conversation_context(
        self, 
        user_message: str, 
        ai_response: str,
        function_calls: List[Dict] = None,
        tool_responses: List[Dict] = None
    ) -> str:
        """Prepare the conversation context for analysis."""
        context = f"""CONVERSATION CYCLE ANALYSIS

USER MESSAGE:
{user_message}

AI RESPONSE:
{ai_response}
"""
        
        if function_calls:
            context += "\nFUNCTION CALLS MADE:\n"
            for i, call in enumerate(function_calls):
                context += f"{i+1}. {call.get('name', 'unknown')}({call.get('arguments', {})})\n"
        
        if tool_responses:
            context += "\nTOOL RESPONSES:\n"
            for i, response in enumerate(tool_responses):
                # Handle complex responses safely
                response_str = str(response)
                if isinstance(response, dict):
                    if 'function' in response and response['function'] == 'generate_image':
                        # Extract key info from image generation
                        result = response.get('result', {})
                        if isinstance(result, str) and 'file_path' in result:
                            context += f"{i+1}. Image generated and saved to media folder\n"
                        elif isinstance(result, dict):
                            file_path = result.get('file_path', 'unknown')
                            prompt = result.get('final_prompt', result.get('original_prompt', 'unknown'))
                            context += f"{i+1}. Image generated: {file_path}, prompt: {prompt[:100]}...\n"
                        else:
                            context += f"{i+1}. Image generation response: {str(result)[:100]}...\n"
                    else:
                        context += f"{i+1}. {response_str[:200]}...\n"
                elif "Image generation:" in response_str and "file_path" in response_str:
                    # Parse image generation result from string format
                    try:
                        import re
                        file_path_match = re.search(r"'file_path': '([^']+)'", response_str)
                        prompt_match = re.search(r"'final_prompt': '([^']+)'", response_str)
                        original_prompt_match = re.search(r"'original_prompt': '([^']+)'", response_str)
                        
                        if file_path_match:
                            file_path = file_path_match.group(1)
                            final_prompt = prompt_match.group(1) if prompt_match else None
                            original_prompt = original_prompt_match.group(1) if original_prompt_match else None
                            prompt = final_prompt or original_prompt or "unknown prompt"
                            
                            # Store the actual local file path for the update system
                            context += f"{i+1}. Image generated: ACTUAL_FILE_PATH={file_path}, description: {prompt[:100]}...\n"
                        else:
                            context += f"{i+1}. {response_str[:200]}...\n"
                    except:
                        context += f"{i+1}. {response_str[:200]}...\n"
                else:
                    context += f"{i+1}. {response_str[:200]}...\n"
        
        return context
    
    def _analyze_with_ai(self, conversation_context: str, current_scratchpad: str) -> Dict:
        """Use GPT-4.1-nano to analyze the conversation for updates."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",  # Using available model, can update when gpt-4.1-nano is available
                messages=[
                    {"role": "system", "content": self.update_prompt},
                    {"role": "user", "content": f"""
CONVERSATION TO ANALYZE:
{conversation_context}

CURRENT SCRATCHPAD:
{current_scratchpad}

NO-UPDATE RESTRICTIONS:
{self.no_update_restrictions}

Please analyze this conversation and determine if any updates to the scratchpad are needed.
"""}
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1000
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (in case there's extra text)
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                content = content[start:end]
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            self._log_update_analysis(f"Failed to parse AI response as JSON: {e}", Fore.RED)
            return {"should_update": False, "error": "Invalid JSON response"}
        except Exception as e:
            self._log_update_analysis(f"AI analysis failed: {e}", Fore.RED)
            return {"should_update": False, "error": str(e)}
    
    def apply_updates(self, updates: List[Dict]) -> bool:
        """Apply the proposed updates to the scratchpad.
        
        Args:
            updates: List of update dictionaries from analysis
            
        Returns:
            True if successful, False otherwise
        """
        if not updates:
            return True
            
        try:
            current_content = self._load_current_scratchpad()
            updated_content = current_content
            
            for update in updates:
                updated_content = self._apply_single_update(updated_content, update)
            
            # Write updated content back to file
            with open(self.scratchpad_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            self._log_update_analysis(f"Applied {len(updates)} update(s) to scratchpad", Fore.GREEN)
            return True
            
        except Exception as e:
            self._log_update_analysis(f"Failed to apply updates: {e}", Fore.RED)
            return False
    
    def _apply_single_update(self, content: str, update: Dict) -> str:
        """Apply a single update to the content."""
        action = update.get('action')
        
        if action == 'update' and 'replaces' in update:
            # Replace existing text
            old_text = str(update['replaces'])
            new_text = str(update['content'])
            if old_text in content:
                content = content.replace(old_text, new_text)
                self._log_update_analysis(f"Updated: {old_text[:50]}... → {new_text[:50]}...", Fore.YELLOW)
            
        elif action == 'add':
            # Add new content to appropriate section
            section = update.get('section', '')
            new_content = str(update['content'])
            
            if section in content:
                # Find section and add content
                section_start = content.find(f"## {section}")
                if section_start != -1:
                    # Find next section or end of file
                    next_section = content.find("##", section_start + 3)
                    if next_section == -1:
                        content += f"\n{new_content}"
                    else:
                        content = content[:next_section] + f"\n{new_content}\n\n" + content[next_section:]
                    self._log_update_analysis(f"Added to {section}: {new_content[:50]}...", Fore.YELLOW)
            
        elif action == 'remove':
            # Remove existing text
            text_to_remove = str(update['content'])
            if text_to_remove in content:
                content = content.replace(text_to_remove, '')
                self._log_update_analysis(f"Removed: {text_to_remove[:50]}...", Fore.YELLOW)
        
        return content


def analyze_conversation(
    user_message: str,
    ai_response: str, 
    function_calls: List[Dict] = None,
    tool_responses: List[Dict] = None
) -> Dict:
    """Convenience function to analyze a conversation for updates.
    
    Returns:
        Analysis result with any proposed updates
    """
    manager = ScratchpadUpdateManager()
    return manager.analyze_conversation_for_updates(
        user_message, ai_response, function_calls, tool_responses
    )


def apply_conversation_updates(
    user_message: str,
    ai_response: str, 
    function_calls: List[Dict] = None,
    tool_responses: List[Dict] = None
) -> bool:
    """Analyze conversation and apply any recommended updates.
    
    Returns:
        True if analysis completed successfully (regardless of whether updates were made)
    """
    try:
        manager = ScratchpadUpdateManager()
        
        # Analyze conversation
        analysis = manager.analyze_conversation_for_updates(
            user_message, ai_response, function_calls, tool_responses
        )
        
        # Apply updates if recommended
        if analysis.get('should_update', False) and 'updates' in analysis:
            return manager.apply_updates(analysis['updates'])
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}[UPDATE] Failed to process updates: {e}{Style.RESET_ALL}")
        return False  # KISS: Don't crash on update failures 