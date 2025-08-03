#!/usr/bin/env python3
"""
Simple chat POC with Gemini 2.0 Flash and DALL-E image generation tool.
Goal: Test how the model handles tool calling and context management.
"""

import os
import sys
import json
import uuid
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import google.generativeai as genai
from openai import OpenAI  # Still needed for DALL-E
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'

class ImageGenPOC:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Still need OpenAI for DALL-E
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        self.media_dir = Path(__file__).parent / "media"
        self.context_dir = Path(__file__).parent / "context"
        self.media_dir.mkdir(exist_ok=True)
        self.context_dir.mkdir(exist_ok=True)
        
        # Session management
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.snapshot_file = self.context_dir / f"context_snapshot_{self.session_id}.md"
        self.api_call_count = 0
        
        # Load configuration from file
        self.config = self._load_config()
        
        # Configurable parameters - loaded from config.json
        self.system_prompt = self.config["system_prompt"]
        self.tool_description = self.config["tool_description"]
        self.parameter_description = self.config["parameter_description"]

        self.model = "gemini-2.0-flash-exp"
        
        # DALL-E settings - lowest quality for speed
        self.image_model = "dall-e-3"
        self.image_size = "1024x1024"
        self.image_quality = "standard"  # lowest quality
        
        self.conversation_history = []
        
        # Initialize persistent Gemini chat session
        self.gemini_chat = self.gemini_model.start_chat(
            history=[],
            enable_automatic_function_calling=False
        )
        
        # Initialize context snapshot
        self._init_context_snapshot()
    
    def _load_config(self):
        """Load Gemini configuration from config.json"""
        config_file = Path(__file__).parent / "config.json"
        try:
            with open(config_file, 'r') as f:
                full_config = json.load(f)
            return full_config["gemini"]
        except FileNotFoundError:
            # Fallback to default config
            return {
                "system_prompt": "You are a helpful assistant that can generate images when requested. When a user asks for an image, use the generate_image tool to create it.",
                "tool_description": "Generate an image based on a text description using DALL-E",
                "parameter_description": "Detailed description of the image to generate"
            }
    
    def _init_context_snapshot(self):
        """Initialize the context snapshot file"""
        with open(self.snapshot_file, 'w') as f:
            f.write(f"# Context Snapshot - Session {self.session_id}\n\n")
            f.write(f"**Started:** {datetime.now().isoformat()}\n\n")
            f.write("## Configuration\n\n")
            f.write(f"- **Model:** {self.model}\n")
            f.write(f"- **Image Model:** {self.image_model}\n")
            f.write(f"- **System Prompt:** {self.system_prompt}\n")
            f.write(f"- **Tool Description:** {self.tool_description}\n\n")
            f.write("## API Calls\n\n")
    
    def _log_context_snapshot(self, messages: List[Dict], response: Any, call_type: str):
        """Log the full context sent to the model"""
        self.api_call_count += 1
        
        with open(self.snapshot_file, 'a') as f:
            f.write(f"### Call #{self.api_call_count} - {call_type} ({datetime.now().strftime('%H:%M:%S')})\n\n")
            
            f.write("**Messages sent to model:**\n```json\n")
            f.write(json.dumps(messages, indent=2, ensure_ascii=False))
            f.write("\n```\n\n")
            
            f.write("**Model Response:**\n```json\n")
            if hasattr(response, 'model_dump'):
                f.write(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
            else:
                f.write(str(response))
            f.write("\n```\n\n")
            
            if hasattr(response, 'usage') and response.usage:
                f.write(f"**Token Usage:** {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion = {response.usage.total_tokens} total\n\n")
            
            f.write("---\n\n")
    
    def _trace(self, message: str, color: str = Colors.WHITE, prefix: str = ""):
        """Print colored trace message"""
        print(f"{color}{prefix}{message}{Colors.RESET}")
    
    def generate_image_tool(self, description: str) -> Dict[str, Any]:
        """Tool function to generate images with DALL-E"""
        self._trace(f"🎨 DALL-E API Call: '{description[:50]}...'", Colors.MAGENTA, "    ")
        
        try:
            response = self.openai_client.images.generate(
                model=self.image_model,
                prompt=description,
                size=self.image_size,
                quality=self.image_quality,
                n=1
            )
            
            # Download and save the image
            import requests
            image_url = response.data[0].url
            image_id = str(uuid.uuid4())[:8]
            filename = f"generated_{image_id}.png"
            filepath = self.media_dir / filename
            
            self._trace(f"💾 Downloading image: {filename}", Colors.CYAN, "    ")
            img_response = requests.get(image_url)
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            self._trace(f"✅ Image saved: {filename}", Colors.GREEN, "    ")
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "description": description,
                "url": image_url
            }
        except Exception as e:
            self._trace(f"❌ DALL-E Error: {str(e)}", Colors.RED, "    ")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tools_definition(self) -> List[Any]:
        """Define the tools available to the model (Gemini format)"""
        import google.generativeai as genai
        
        return [genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name="generate_image",
                    description=self.tool_description,
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "description": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description=self.parameter_description
                            )
                        },
                        required=["description"]
                    )
                )
            ]
        )]
    
    def handle_tool_call(self, tool_call) -> str:
        """Handle tool calls from the model (Gemini format)"""
        if tool_call.name == "generate_image":
            description = tool_call.args["description"]
            result = self.generate_image_tool(description)
            
            if result["success"]:
                return f"Image generated successfully and saved to {result['filename']}. Description: {result['description']}"
            else:
                return f"Error generating image: {result['error']}"
        
        return "Unknown tool call"
    
    def chat(self, user_message: str) -> str:
        """Process a chat message and return the response (Gemini version)"""
        self._trace(f"\n📥 User Input: '{user_message}'", Colors.BLUE, "")
        
        try:
            # Add user message to our history tracking
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # For the first message, include system prompt
            if len(self.conversation_history) == 1:
                message_to_send = f"{self.system_prompt}\n\nUser: {user_message}"
            else:
                message_to_send = user_message
            
            self._trace(f"🤖 Calling {self.model} (context: {len(self.conversation_history)} messages)", Colors.YELLOW, "  ")
            
            # Send message to persistent chat session
            response = self.gemini_chat.send_message(
                message_to_send,
                tools=self.get_tools_definition()
            )
            
            # Log to context snapshot
            messages_for_log = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
            self._log_context_snapshot(messages_for_log, response, "Gemini Chat")
            
            # Show token usage if available
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                self._trace(f"📊 Tokens: {response.usage_metadata.prompt_token_count}→{response.usage_metadata.candidates_token_count} (total: {response.usage_metadata.total_token_count})", Colors.DIM, "  ")
            
            # Check if the model wants to use tools
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        func_call = part.function_call
                        self._trace(f"🔧 Model wants to use tool: {func_call.name}", Colors.CYAN, "  ")
                        
                        # Show tool call details
                        args_str = ', '.join([f'{k}={repr(v)[:30]}...' if len(repr(v)) > 30 else f'{k}={repr(v)}' for k, v in func_call.args.items()])
                        self._trace(f"  Tool: {func_call.name}({args_str})", Colors.YELLOW, "  ")
                        
                        # Add assistant message with tool call to history
                        self.conversation_history.append({
                            "role": "assistant", 
                            "content": None,
                            "tool_calls": [{"name": func_call.name, "args": dict(func_call.args)}]
                        })
                        
                        # Execute the tool
                        self._trace(f"⚡ Executing: {func_call.name}", Colors.MAGENTA, "  ")
                        tool_result = self.handle_tool_call(func_call)
                        
                        # Add tool result to history
                        self.conversation_history.append({
                            "role": "tool",
                            "content": tool_result
                        })
                        
                        # Send tool result back to model
                        self._trace(f"🤖 Sending tool result back to {self.model}", Colors.YELLOW, "  ")
                        
                        # Create function response
                        function_response = genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=func_call.name,
                                response={"result": tool_result}
                            )
                        )
                        
                        # Send the function response to persistent chat
                        final_response = self.gemini_chat.send_message([function_response])
                        
                        # Log final response
                        final_messages_for_log = messages_for_log + [{"role": "tool", "content": tool_result}]
                        self._log_context_snapshot(final_messages_for_log, final_response, "Post-Tool Response")
                        
                        # Add final assistant response to history
                        final_text = final_response.text
                        self.conversation_history.append({"role": "assistant", "content": final_text})
                        
                        # Show final token usage
                        if hasattr(final_response, 'usage_metadata') and final_response.usage_metadata:
                            self._trace(f"📊 Final tokens: {final_response.usage_metadata.prompt_token_count}→{final_response.usage_metadata.candidates_token_count} (total: {final_response.usage_metadata.total_token_count})", Colors.DIM, "  ")
                        
                        self._trace(f"✅ Response ready", Colors.GREEN, "  ")
                        return final_text
                
                # No tool calls, just regular response
                self._trace(f"💬 Direct response (no tools)", Colors.GREEN, "  ")
                response_text = response.text
                self.conversation_history.append({"role": "assistant", "content": response_text})
                return response_text
                
        except Exception as e:
            self._trace(f"❌ Chat Error: {str(e)}", Colors.RED, "  ")
            return f"Error: {str(e)}"
    
    def print_config(self):
        """Print current configuration for easy debugging"""
        print(f"{Colors.BOLD}=== Current Configuration ==={Colors.RESET}")
        print(f"{Colors.CYAN}Session ID:{Colors.RESET} {self.session_id}")
        print(f"{Colors.CYAN}Context Log:{Colors.RESET} {self.snapshot_file}")
        print(f"{Colors.CYAN}API Calls:{Colors.RESET} {self.api_call_count}")
        print(f"{Colors.CYAN}Model:{Colors.RESET} {self.model}")
        print(f"{Colors.CYAN}Image Model:{Colors.RESET} {self.image_model}")
        print(f"{Colors.CYAN}Image Size:{Colors.RESET} {self.image_size}")
        print(f"{Colors.CYAN}Image Quality:{Colors.RESET} {self.image_quality}")
        print(f"{Colors.CYAN}Media Directory:{Colors.RESET} {self.media_dir}")
        print(f"{Colors.CYAN}Context Directory:{Colors.RESET} {self.context_dir}")
        print(f"{Colors.CYAN}System Prompt:{Colors.RESET} {self.system_prompt}")
        print(f"{Colors.CYAN}Tool Description:{Colors.RESET} {self.tool_description}")
        print(f"{Colors.BOLD}{'=' * 30}{Colors.RESET}")
    
    def cleanup_temp_files(self):
        """Clean up all temporary files (media and context)"""
        files_removed = 0
        
        # Clean media files
        if self.media_dir.exists():
            for img_file in self.media_dir.glob("*.png"):
                img_file.unlink()
                files_removed += 1
            print(f"{Colors.GREEN}🗑️  Removed {files_removed} media files{Colors.RESET}")
        
        # Clean context files
        if self.context_dir.exists():
            context_files = list(self.context_dir.glob("context_snapshot_*.md"))
            for ctx_file in context_files:
                ctx_file.unlink()
                files_removed += 1
            print(f"{Colors.GREEN}🗑️  Removed {len(context_files)} context files{Colors.RESET}")
        
        print(f"{Colors.BOLD}✨ Cleanup complete: {files_removed} files removed{Colors.RESET}")
        return files_removed

def main():
    """Simple interactive chat loop"""
    parser = argparse.ArgumentParser(description="Gemini 2.0 Flash + DALL-E Image Generation POC")
    parser.add_argument('--clean', action='store_true', 
                       help='Clean up all temporary files (media and context) and exit')
    args = parser.parse_args()
    
    poc = ImageGenPOC()
    
    if args.clean:
        print(f"{Colors.BOLD}🧹 Cleaning up before starting...{Colors.RESET}")
        files_removed = poc.cleanup_temp_files()
        if files_removed == 0:
            print(f"{Colors.YELLOW}No temporary files found to clean{Colors.RESET}")
        print(f"{Colors.GREEN}Starting fresh session...{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}🤖 Gemini 2.0 Flash + DALL-E Image Generation POC{Colors.RESET}")
    print(f"{Colors.DIM}Session: {poc.session_id}{Colors.RESET}")
    print(f"{Colors.GREEN}Commands:{Colors.RESET} 'config' (settings), 'trace' (toggle), 'clean' (cleanup), 'quit' (exit)")
    print("-" * 70)
    
    poc.print_config()
    
    trace_enabled = True
    
    while True:
        try:
            user_input = input(f"\n{Colors.BOLD}👤 You:{Colors.RESET} ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"{Colors.GREEN}📊 Session Summary:{Colors.RESET}")
                print(f"  • API Calls: {poc.api_call_count}")
                print(f"  • Context Log: {poc.snapshot_file}")
                print(f"  • Media Files: {len(list(poc.media_dir.glob('*.png')))} images")
                print("Goodbye!")
                break
            elif user_input.lower() == 'config':
                poc.print_config()
                continue
            elif user_input.lower() == 'trace':
                trace_enabled = not trace_enabled
                print(f"{Colors.YELLOW}Trace mode: {'ON' if trace_enabled else 'OFF'}{Colors.RESET}")
                continue
            elif user_input.lower() == 'clean':
                files_removed = poc.cleanup_temp_files()
                if files_removed == 0:
                    print(f"{Colors.YELLOW}No temporary files found to clean{Colors.RESET}")
                continue
            elif not user_input:
                continue
            
            print(f"{Colors.BOLD}🤖 Assistant:{Colors.RESET}")
            if not trace_enabled:
                # Temporarily disable tracing
                old_trace = poc._trace
                poc._trace = lambda *_args, **_kwargs: None
            
            response = poc.chat(user_input)
            
            if not trace_enabled:
                poc._trace = old_trace
                print(f"  {response}")
            else:
                print(f"📤 {response}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}Goodbye!{Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()