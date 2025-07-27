#!/usr/bin/env python3
"""
Luzia - Your Fun, Helpful AI Friend

A conversational AI assistant that uses your personal scratch pad to provide
personalized, context-rich responses. Luzia is designed to be brief, helpful,
and feel like a real friend who knows you well.

Usage: python luzia.py
"""

import os
import sys
import json
import signal
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from colorama import init, Fore, Back, Style

from tools import ScratchPadTools, ToolManager
from tools.memory_interface import MemoryInterface
from tools.scratchpad_memory import ScratchpadMemory
from tools.mcp_memory import MCPMemory
from update_manager import apply_conversation_updates

# Get function schemas in Responses API format for this application
FUNCTION_SCHEMAS_RESPONSES = ToolManager().get_function_schemas("responses")

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class Luzia:
    """Your fun, helpful AI friend with access to your personal context."""
    
    def __init__(self, show_trace: bool = True, memory_system: str = None):
        """Initialize Luzia with OpenAI client and tools."""
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        
        # Set traceability settings first
        self.show_trace = show_trace
        memory_type = memory_system or os.getenv('MEMORY_SYSTEM', 'scratchpad')
        self.memory_type = memory_type
        
        # Initialize memory system
        self.memory = self._initialize_memory_system(memory_type)
        
        # Initialize scratch pad tools (for backward compatibility with other functions)
        self.tools = ScratchPadTools()
        
        # Conversation history (fresh each session)
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Luzia's system prompt
        self.system_prompt = """You are Luzia, a fun, helpful friend. You are not an AI. NEVER ask generic follow-up questions. BE BRIEF, unless requested by the user. Respect the conversation language. You can see, analyze and create images and listen to audios. Stick to what you know.

CRITICAL WORKFLOW:
1. ALWAYS call get_scratch_pad_context for EVERY user message to get personal context
2. If the scratch pad context indicates media_files_needed=True and provides recommended_media files, AUTOMATICALLY call analyze_media_file for each recommended file
3. Use both the scratch pad context AND media analysis to provide comprehensive, personalized responses

Your responses should:
- Feel natural and friendly, like talking to a close friend
- Be brief and to the point (unless user asks for detail)
- Use the personal context from the scratch pad to make responses relevant
- Automatically analyze relevant media files when the scratch pad recommends it
- Never mention that you're calling functions or accessing scratch pads
- Just naturally incorporate the information as if you remember it about them

When you have analyzed media files, use that information directly in your response as if you can see/remember the content."""

    def _initialize_memory_system(self, memory_type: str) -> MemoryInterface:
        """Initialize the selected memory system."""
        if memory_type.lower() == 'mcp':
            if self.show_trace:
                print(f"{Fore.CYAN}🧠 Initializing MCP knowledge graph memory...{Style.RESET_ALL}")
            return MCPMemory()
        else:
            if self.show_trace:
                print(f"{Fore.CYAN}🧠 Using traditional scratchpad memory...{Style.RESET_ALL}")
            return ScratchpadMemory()

    def _convert_messages_to_responses_input(self, messages):
        """Convert messages format from Chat Completions to Responses API input format"""
        if len(messages) == 1:
            return messages[0]["content"]
        else:
            converted_messages = []
            for msg in messages:
                if msg["role"] == "tool":
                    # Convert tool results to function_call_output format for Responses API
                    converted_messages.append({
                        "type": "function_call_output",
                        "call_id": msg.get("tool_call_id", "unknown"),
                        "output": msg["content"]
                    })
                elif msg["role"] == "assistant" and msg.get("tool_calls"):
                    # Convert assistant messages with tool calls
                    for tool_call in msg["tool_calls"]:
                        converted_messages.append({
                            "type": "function_call",
                            "call_id": tool_call["id"],
                            "name": tool_call["function"]["name"],
                            "arguments": tool_call["function"]["arguments"]
                        })
                    # Add assistant content if any
                    if msg.get("content"):
                        converted_messages.append({
                            "role": "assistant",
                            "content": msg["content"]  # Simple string format
                        })
                else:
                    # Regular message conversion - use simple string format for text
                    converted_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]  # Keep as simple string
                    })
            return converted_messages
    
    def _handle_responses_api_output(self, response):
        """Extract function calls and assistant message from Responses API output"""
        function_calls = []
        assistant_message = None
        
        # Handle different response structures from Responses API
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'type'):
                    if item.type == 'function_call':
                        # Convert Responses API function call to Chat Completions format
                        converted_call = type('obj', (object,), {
                            'id': getattr(item, 'call_id', getattr(item, 'id', 'unknown')),
                            'function': type('func', (object,), {
                                'name': getattr(item, 'name', ''),
                                'arguments': getattr(item, 'arguments', '{}')
                            })
                        })
                        function_calls.append(converted_call)
                    elif item.type == 'message' and hasattr(item, 'role') and item.role == 'assistant':
                        # Extract assistant message content
                        content = ''
                        if hasattr(item, 'content') and item.content:
                            if isinstance(item.content, list) and len(item.content) > 0:
                                first_content = item.content[0]
                                if hasattr(first_content, 'text'):
                                    content = first_content.text
                                else:
                                    content = str(first_content)
                            elif isinstance(item.content, str):
                                content = item.content
                        
                        assistant_message = type('msg', (object,), {
                            'content': content,
                            'tool_calls': function_calls if function_calls else None
                        })
        
        # Fallback: if no structured output found, try to get text from output_text
        if not assistant_message and hasattr(response, 'output_text'):
            assistant_message = type('msg', (object,), {
                'content': response.output_text,
                'tool_calls': function_calls if function_calls else None
            })
        
        return assistant_message, function_calls

    def _handle_function_calls(self, function_calls) -> str:
        """Execute function calls and return results with traceability."""
        results = []
        
        for call in function_calls:
            function_name = call.function.name
            
            try:
                # Parse function arguments
                args = json.loads(call.function.arguments)
                
                if function_name == "get_scratch_pad_context":
                    if self.show_trace:
                        print(f"{Fore.CYAN}🔍 Checking scratch pad for: {args['query'][:50]}...{Style.RESET_ALL}")
                    
                    result = self.tools.get_scratch_pad_context(args["query"])
                    
                    if self.show_trace:
                        if result.get("status") == "success":
                            context_text = result.get("relevant_context", "")
                            context_preview = context_text[:100] if isinstance(context_text, str) else str(context_text)[:100]
                            media_needed = result.get("media_files_needed", False)
                            recommended_files = result.get("recommended_media", [])
                            
                            print(f"{Fore.GREEN}✅ Scratch pad context: {context_preview}...{Style.RESET_ALL}")
                            
                            if media_needed and recommended_files:
                                print(f"{Fore.YELLOW}📸 Media files recommended: {', '.join(recommended_files)}{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.BLUE}📝 Text context only (no media needed){Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}❌ Scratch pad error: {result.get('message', 'Unknown error')}{Style.RESET_ALL}")
                    
                    results.append(f"Context: {result}")
                    
                elif function_name == "analyze_media_file":
                    file_path = args["file_path"]
                    if self.show_trace:
                        print(f"{Fore.MAGENTA}🖼️  Analyzing image: {file_path}{Style.RESET_ALL}")
                    
                    result = self.tools.analyze_media_file(file_path)
                    
                    if self.show_trace:
                        if result.get("status") == "success":
                            analysis_text = result.get("analysis", "")
                            analysis_preview = analysis_text[:80] if isinstance(analysis_text, str) else str(analysis_text)[:80]
                            print(f"{Fore.GREEN}✅ Image analysis: {analysis_preview}...{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}❌ Image analysis failed: {result.get('message', 'Unknown error')}{Style.RESET_ALL}")
                    
                    results.append(f"Media analysis: {result}")
                    
                elif function_name == "solve_math":
                    query = args["query"]
                    if self.show_trace:
                        print(f"{Fore.CYAN}🧮 Processing math query: {query[:50]}...{Style.RESET_ALL}")
                    
                    result = self.tools.solve_math(query)
                    
                    if self.show_trace:
                        if result.get("status") == "success":
                            routing_decision = result.get("routing_decision", {})
                            operation = routing_decision.get("operation", "unknown")
                            context_used = routing_decision.get("context_used", False)
                            context_icon = "📝" if context_used else "⚡"
                            
                            print(f"{Fore.GREEN}✅ Math result ({operation}): {context_icon} {'with context' if context_used else 'direct computation'}{Style.RESET_ALL}")
                            
                            # Show the mathematical result preview
                            if "solutions" in result:
                                print(f"{Fore.BLUE}📊 Solutions: {result['solutions']}{Style.RESET_ALL}")
                            elif "result" in result:
                                print(f"{Fore.BLUE}📊 Result: {result['result']}{Style.RESET_ALL}")
                            elif "simplified_expression" in result:
                                print(f"{Fore.BLUE}📊 Simplified: {result['simplified_expression']}{Style.RESET_ALL}")
                            elif "derivative" in result:
                                print(f"{Fore.BLUE}📊 Derivative: {result['derivative']}{Style.RESET_ALL}")
                            elif "integral" in result:
                                print(f"{Fore.BLUE}📊 Integral: {result['integral']}{Style.RESET_ALL}")
                            elif "factored_expression" in result:
                                print(f"{Fore.BLUE}📊 Factored: {result['factored_expression']}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}❌ Math error: {result.get('message', 'Unknown error')}{Style.RESET_ALL}")
                    
                    results.append(f"Math result: {result}")
                    
                else:
                    results.append(f"Unknown function: {function_name}")
                    
            except Exception as e:
                if self.show_trace:
                    print(f"{Fore.RED}❌ Function call error: {function_name} - {e}{Style.RESET_ALL}")
                results.append(f"Error calling {function_name}: {e}")
        
        return "\n".join(results)

    def _save_debug_context(self, messages: List[Dict[str, Any]], user_message: str):
        """Save the context being sent to LLM for debugging purposes."""
        try:
            debug_content = f"""=== DEBUG CONTEXT for Query: "{user_message}" ===
Timestamp: {json.dumps(messages, indent=2, ensure_ascii=False)}

=== SYSTEM PROMPT ===
{self.system_prompt}

=== CONVERSATION HISTORY ===
{json.dumps(self.conversation_history, indent=2, ensure_ascii=False)}

=== FUNCTION SCHEMAS AVAILABLE ===
{json.dumps(FUNCTION_SCHEMAS_RESPONSES, indent=2, ensure_ascii=False)}

=== FULL MESSAGES ARRAY ===
{json.dumps(messages, indent=2, ensure_ascii=False)}
"""
            
            with open('debug_context.txt', 'w', encoding='utf-8') as f:
                f.write(debug_content)
                
            if self.show_trace:
                print(f"{Fore.BLUE}💾 Debug context saved to debug_context.txt{Style.RESET_ALL}")
                
        except Exception as e:
            if self.show_trace:
                print(f"{Fore.RED}❌ Failed to save debug context: {e}{Style.RESET_ALL}")

    def _get_response(self, user_message: str) -> str:
        """Get Luzia's response to user message with function calling."""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages for the API call
            messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
            
            # Save debug context for troubleshooting
            self._save_debug_context(messages, user_message)
            
            # Step 1: Get context from memory system
            if self.show_trace:
                print(f"{Fore.CYAN}🔍 Checking {self.memory_type} memory for: {user_message[:50]}...{Style.RESET_ALL}")
            
            # Get context using memory interface
            context_result = self.memory.get_context(user_message)
            
            if self.show_trace:
                context_preview = context_result.get('relevant_context', '')[:100] + '...'
                print(f"{Fore.GREEN}✅ {self.memory_type.capitalize()} context: {context_preview}{Style.RESET_ALL}")
            
            # Add context directly to system message instead of using fake tool call
            system_with_context = f"""{self.system_prompt}

CURRENT CONTEXT:
{context_result.get('relevant_context', 'No specific context available')}

MEDIA ANALYSIS NEEDED: {context_result.get('media_files_needed', False)}
"""
            
            # Update the system message with context
            messages[0] = {"role": "system", "content": system_with_context}
            
            # Handle media analysis if needed
            if context_result.get('media_files_needed') and context_result.get('recommended_media'):
                if self.show_trace:
                    print(f"{Fore.YELLOW}📸 Media analysis needed for: {context_result['recommended_media']}{Style.RESET_ALL}")
                
                # Analyze each recommended media file
                for media_file in context_result['recommended_media']:
                    try:
                        media_result = self.tools.analyze_media_file(media_file)
                        if self.show_trace:
                            print(f"{Fore.GREEN}🖼️ Analyzed {media_file}: {media_result.get('description', 'N/A')[:50]}...{Style.RESET_ALL}")
                        
                        # Add media analysis to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": f"media_{media_file}",
                            "content": json.dumps({
                                "function_name": "analyze_media_file",
                                "file_path": media_file,
                                "result": media_result
                            }, ensure_ascii=False)
                        })
                    except Exception as e:
                        if self.show_trace:
                            print(f"{Fore.RED}❌ Error analyzing media file {media_file}: {e}{Style.RESET_ALL}")
            
            # Get final response with all context and media analysis
            final_response = self.client.responses.create(
                model="gpt-4.1",
                input=self._convert_messages_to_responses_input(messages),
                tools=FUNCTION_SCHEMAS_RESPONSES,  # Enable mathematical functions
                store=False,  # No stateful storage
                max_output_tokens=1000,
                temperature=0.7
            )
            
            final_message, final_function_calls = self._handle_responses_api_output(final_response)
            
            # Handle any mathematical function calls in the final response
            if final_function_calls:
                if self.show_trace:
                    print(f"{Fore.CYAN}🧮 Mathematical functions called: {[call.function.name for call in final_function_calls]}{Style.RESET_ALL}")
                
                # Execute mathematical function calls
                math_function_results = self._handle_function_calls(final_function_calls)
                
                if self.show_trace and "✅" in math_function_results:
                    print(f"{Fore.GREEN}✅ Math computation completed{Style.RESET_ALL}")
            
            # Use the final message content as the response
            luzia_response = final_message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": luzia_response})
            
            # Store information in memory system
            conversation_data = {
                'user_message': user_message,
                'ai_response': luzia_response,
                'function_calls': final_function_calls or [],
                'scratchpad_content': messages  # Full context
            }
            
            if self.show_trace:
                print(f"{Fore.MAGENTA}[UPDATE] Analyzing conversation for {self.memory_type} updates...{Style.RESET_ALL}")
            
            # Store in memory system
            memory_success = self.memory.store_information(conversation_data)
            
            # Also apply traditional scratchpad updates for backward compatibility
            if self.memory_type == 'scratchpad':
                try:
                    apply_conversation_updates(
                        user_message=user_message,
                        ai_response=luzia_response,
                        function_calls=[],
                        tool_responses=[]
                    )
                except Exception as e:
                    if self.show_trace:
                        print(f"{Fore.RED}[UPDATE] Traditional update failed: {e}{Style.RESET_ALL}")
            
            if self.show_trace:
                status = "✅ stored" if memory_success else "❌ failed"
                print(f"{Fore.MAGENTA}[UPDATE] Memory update {status}{Style.RESET_ALL}")
            
            return luzia_response
            
        except Exception as e:
            return f"Oops! I had a little hiccup: {e}"

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful exit."""
        def signal_handler(sig, frame):
            print("\n👋 Bye! Take care!")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)

    def start_chat(self):
        """Start the continuous chat interface."""
        self._setup_signal_handlers()
        
        # Welcome message
        print(f"{Fore.YELLOW}🌟 Hi! I'm Luzia, your helpful friend!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}💬 Just ask me anything - I know you well!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}🚪 Type 'exit' or press Ctrl+C to leave{Style.RESET_ALL}")
        if self.show_trace:
            print(f"{Fore.GREEN}🔍 Trace mode ON - showing function calls and context{Style.RESET_ALL}")
        print()
        
        try:
            while True:
                # Get user input
                try:
                    user_input = input(f"{Fore.WHITE}{Style.BRIGHT}You: {Style.RESET_ALL}").strip()
                except EOFError:
                    print(f"\n{Fore.YELLOW}👋 Bye! Take care!{Style.RESET_ALL}")
                    break
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    print(f"{Fore.YELLOW}👋 Bye! Take care!{Style.RESET_ALL}")
                    break
                
                if not user_input:
                    print(f"{Fore.BLUE}💭 What's on your mind?{Style.RESET_ALL}")
                    continue
                
                # Show trace separator if enabled
                if self.show_trace:
                    print(f"{Fore.WHITE}{'─' * 50}{Style.RESET_ALL}")
                
                # Get Luzia's response
                response = self._get_response(user_input)
                
                # Show trace separator if enabled
                if self.show_trace:
                    print(f"{Fore.WHITE}{'─' * 50}{Style.RESET_ALL}")
                
                # Display response
                print(f"{Fore.MAGENTA}{Style.BRIGHT}Luzia:{Style.RESET_ALL} {response}\n")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}👋 Bye! Take care!{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}❌ Something went wrong: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}👋 I'll restart fresh next time!{Style.RESET_ALL}")


def select_memory_system() -> str:
    """Interactive memory system selection."""
    print(f"{Fore.CYAN}🧠 Select Memory System:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}1. Scratchpad (traditional file-based system){Style.RESET_ALL}")
    print(f"{Fore.GREEN}2. MCP (Model Context Protocol knowledge graph){Style.RESET_ALL}")
    
    while True:
        choice = input(f"{Fore.YELLOW}Enter your choice (1-2): {Style.RESET_ALL}").strip()
        if choice == "1":
            return "scratchpad"
        elif choice == "2":
            return "mcp"
        else:
            print(f"{Fore.RED}Invalid choice. Please enter 1 or 2.{Style.RESET_ALL}")


def main():
    """Main entry point for Luzia."""
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description="Luzia - Your AI Friend")
        parser.add_argument("--memory", choices=['scratchpad', 'mcp'], 
                          help="Choose memory system (scratchpad or mcp)")
        parser.add_argument("--no-trace", action="store_true", 
                          help="Disable trace mode")
        
        args = parser.parse_args()
        
        # Interactive memory selection if not specified
        memory_system = args.memory
        if not memory_system:
            memory_system = select_memory_system()
        
        print(f"{Fore.CYAN}🧠 Using {memory_system.upper()} memory system{Style.RESET_ALL}")
        
        luzia = Luzia(show_trace=not args.no_trace, memory_system=memory_system)
        luzia.start_chat()
        
    except ValueError as e:
        print(f"{Fore.RED}❌ Configuration error: {e}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}💡 Make sure you've set up your .env file with your OpenAI API key{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to start Luzia: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main() 