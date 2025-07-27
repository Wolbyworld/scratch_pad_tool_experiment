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

from tools import ScratchPadTools, FUNCTION_SCHEMAS
from update_manager import apply_conversation_updates

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class Luzia:
    """Your fun, helpful AI friend with access to your personal context."""
    
    def __init__(self, show_trace: bool = True):
        """Initialize Luzia with OpenAI client and tools."""
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        
        # Initialize scratch pad tools
        self.tools = ScratchPadTools()
        
        # Conversation history (fresh each session)
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Traceability settings
        self.show_trace = show_trace
        
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
                            "content": [{"type": "input_text", "text": msg["content"]}]
                        })
                else:
                    # Regular message conversion
                    content = msg["content"]
                    if isinstance(content, str):
                        content = [{"type": "input_text", "text": content}]
                    converted_messages.append({
                        "role": msg["role"],
                        "content": content
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
{json.dumps(FUNCTION_SCHEMAS, indent=2, ensure_ascii=False)}

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
            
            # Step 1: Always call get_scratch_pad_context first
            response = self.client.responses.create(
                model="gpt-4.1",  # Using GPT-4.1 as specified
                input=self._convert_messages_to_responses_input(messages),
                tools=FUNCTION_SCHEMAS,
                tool_choice={
                    "type": "function",
                    "name": "get_scratch_pad_context"
                },  # Force calling the required scratch pad context function
                store=False,  # CRITICAL: No stateful storage
                max_output_tokens=1000,
                temperature=0.7
            )
            
            assistant_message, function_calls = self._handle_responses_api_output(response)
            scratch_pad_results = None
            
            # Handle the scratch pad function call
            if function_calls:
                # Execute the scratch pad function call
                function_results = self._handle_function_calls(function_calls)
                scratch_pad_results = function_results
                
                # Add function call message to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments
                            }
                        } for call in function_calls
                    ]
                })
                
                # Add function results to history
                for i, call in enumerate(function_calls):
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": function_results.split("\n")[i] if i < len(function_results.split("\n")) else ""
                    })
                
                # Step 2: Check if media analysis is needed and make second call
                if "media_files_needed" in function_results and "recommended_media" in function_results:
                    # Parse the scratch pad results to get recommended media files
                    try:
                        # Extract recommended media files from the results
                        media_match = re.search(r"'recommended_media': \[(.*?)\]", function_results)
                        if media_match:
                            media_files_str = media_match.group(1)
                            # Extract file paths (simple parsing for quoted strings)
                            media_files = [f.strip().strip("'\"") for f in media_files_str.split(",") if f.strip().strip("'\"")]
                            
                            if media_files:
                                if self.show_trace:
                                    print(f"{Fore.YELLOW}🖼️  Auto-analyzing recommended media files...{Style.RESET_ALL}")
                                
                                # Call analyze_media_file for each recommended file
                                for media_file in media_files:
                                    if media_file:  # Skip empty strings
                                        # Create a mock tool call for media analysis
                                        media_result = self.tools.analyze_media_file(media_file)
                                        
                                        if self.show_trace:
                                            if media_result.get("status") == "success":
                                                analysis_text = media_result.get("analysis", "")
                                                analysis_preview = analysis_text[:80] if isinstance(analysis_text, str) else str(analysis_text)[:80]
                                                print(f"{Fore.GREEN}✅ Image analysis: {analysis_preview}...{Style.RESET_ALL}")
                                            else:
                                                print(f"{Fore.RED}❌ Image analysis failed: {media_result.get('message', 'Unknown error')}{Style.RESET_ALL}")
                                        
                                        # Add media analysis to conversation history as assistant message
                                        media_analysis_text = media_result.get("analysis", "Analysis failed")
                                        self.conversation_history.append({
                                            "role": "assistant", 
                                            "content": f"[INTERNAL] Media analysis of {media_file}: {media_analysis_text}"
                                        })
                    except Exception as e:
                        if self.show_trace:
                            print(f"{Fore.RED}❌ Error parsing media recommendations: {e}{Style.RESET_ALL}")
                
                # Get final response with all function results (INCLUDING mathematical functions)
                final_response = self.client.responses.create(
                    model="gpt-4.1",
                    input=self._convert_messages_to_responses_input([{"role": "system", "content": self.system_prompt}] + self.conversation_history),
                    tools=FUNCTION_SCHEMAS,  # ✅ CRITICAL FIX: Enable mathematical functions
                    store=False,  # CRITICAL: No stateful storage
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
                    
                    # Add function call to conversation history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": final_message.content,
                        "tool_calls": [
                            {
                                "id": call.id,
                                "type": "function", 
                                "function": {
                                    "name": call.function.name,
                                    "arguments": call.function.arguments
                                }
                            } for call in final_function_calls
                        ]
                    })
                    
                    # Add function results to conversation history
                    for i, call in enumerate(final_function_calls):
                        result_line = math_function_results.split("\n")[i] if i < len(math_function_results.split("\n")) else ""
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result_line
                        })
                    
                    # Generate final natural language response with mathematical results
                    natural_response = self.client.chat.completions.create(
                        model="gpt-4.1",
                        messages=[{"role": "system", "content": self.system_prompt}] + self.conversation_history,
                        max_tokens=1000,
                        temperature=0.7
                    )
                    
                    luzia_response = natural_response.choices[0].message.content
                else:
                    luzia_response = final_message.content
            else:
                luzia_response = assistant_message.content
            
            # Add Luzia's response to conversation history
            self.conversation_history.append({"role": "assistant", "content": luzia_response})
            
            # Analyze conversation for scratchpad updates (runs 100% of the time)
            try:
                # Prepare function call data for update analysis
                function_calls_data = []
                tool_responses_data = []
                
                if function_calls:
                    for call in function_calls:
                        function_calls_data.append({
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        })
                    
                    if scratch_pad_results:
                        tool_responses_data.append({
                            "function": "get_scratch_pad_context", 
                            "result": scratch_pad_results
                        })
                
                # Run update analysis in background (invisible to user, but logged)
                apply_conversation_updates(
                    user_message=user_message,
                    ai_response=luzia_response,
                    function_calls=function_calls_data,
                    tool_responses=tool_responses_data
                )
            except Exception as e:
                # KISS: Don't let update failures break the conversation
                if self.show_trace:
                    print(f"{Fore.RED}[UPDATE] Update analysis failed: {e}{Style.RESET_ALL}")
            
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


def main():
    """Main entry point for Luzia."""
    try:
        # Check for command line arguments
        show_trace = True  # Default to showing trace
        if len(sys.argv) > 1:
            if "--no-trace" in sys.argv:
                show_trace = False
            elif "--help" in sys.argv or "-h" in sys.argv:
                print(f"{Fore.CYAN}Luzia - Your Fun, Helpful AI Friend{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Usage: python luzia.py [options]{Style.RESET_ALL}")
                print(f"{Fore.GREEN}Options:{Style.RESET_ALL}")
                print(f"  --no-trace    Disable function call traceability")
                print(f"  --help, -h    Show this help message")
                return
        
        luzia = Luzia(show_trace=show_trace)
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