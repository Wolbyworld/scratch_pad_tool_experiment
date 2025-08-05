#!/usr/bin/env python3
"""
PDF Document Analysis CLI - Multi-turn Conversation PoC
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from pathlib import Path

try:
    from openai import OpenAI
    from colorama import Fore, Back, Style, init
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required packages. Please install: {e}")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

# Initialize colorama for cross-platform color support
init(autoreset=True)

class Colors:
    """Color constants for CLI output"""
    USER = Fore.CYAN
    ASSISTANT = Fore.GREEN
    SYSTEM = Fore.YELLOW
    DEBUG = Fore.MAGENTA
    ERROR = Fore.RED
    SUCCESS = Fore.GREEN + Style.BRIGHT
    INFO = Fore.BLUE
    TOOL = Fore.YELLOW + Style.BRIGHT
    TOKEN = Fore.WHITE + Style.DIM
    PURPLE = Fore.MAGENTA + Style.BRIGHT
    RESET = Style.RESET_ALL

class PDFChatCLI:
    def __init__(self, config_path: str = "config.json", clean_logs: bool = False):
        """Initialize the PDF Chat CLI"""
        self.config = self._load_config(config_path)
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_history = []
        self.uploaded_files = {}  # Track uploaded files and their IDs
        self.message_count_since_upload = 0
        self.current_file_path = None
        self.logs_dir = Path(".logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Clean logs if requested
        if clean_logs:
            self._clean_logs()
        
        # Initialize conversation with base system prompt
        system_prompt = self.config["openai"]["main_agent"]["system_prompt_base"]
        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Initialize cost tracking
        self.total_cost = 0.0
        self.total_tokens = 0
        
        # Store document context for relevance checking
        self.document_topic = None
        self.document_summary = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{Colors.ERROR}Config file not found: {config_path}{Colors.RESET}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"{Colors.ERROR}Invalid JSON in config file: {e}{Colors.RESET}")
            sys.exit(1)
    
    def _print_debug(self, message: str, color: str = Colors.DEBUG):
        """Print debug information with color coding"""
        print(f"{color}[DEBUG] {message}{Colors.RESET}")
    
    def _print_info(self, message: str, color: str = Colors.INFO):
        """Print info message with color coding"""
        print(f"{color}[INFO] {message}{Colors.RESET}")
    
    def _print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.ERROR}[ERROR] {message}{Colors.RESET}")
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage and model pricing"""
        if model not in self.config["pricing"]:
            self._print_debug(f"No pricing info for model: {model}", Colors.DEBUG)
            return 0.0
        
        pricing = self.config["pricing"][model]
        input_cost = (input_tokens / 1000) * pricing["input_cost_per_1k"]
        output_cost = (output_tokens / 1000) * pricing["output_cost_per_1k"]
        total_cost = input_cost + output_cost
        
        return total_cost
    
    def _print_cost_summary(self, model: str, input_tokens: int, output_tokens: int, cost: float):
        """Print detailed cost breakdown"""
        pricing = self.config["pricing"][model]
        input_cost = (input_tokens / 1000) * pricing["input_cost_per_1k"]
        output_cost = (output_tokens / 1000) * pricing["output_cost_per_1k"]
        
        self._print_debug(f"💰 Cost breakdown for {model}:", Colors.TOKEN)
        self._print_debug(f"  - Input: {input_tokens:,} tokens × ${pricing['input_cost_per_1k']:.6f}/1k = ${input_cost:.6f}", Colors.TOKEN)
        self._print_debug(f"  - Output: {output_tokens:,} tokens × ${pricing['output_cost_per_1k']:.6f}/1k = ${output_cost:.6f}", Colors.TOKEN)
        self._print_debug(f"  - Total: ${cost:.6f}", Colors.TOKEN)
        
        # Update running totals
        self.total_cost += cost
        self.total_tokens += input_tokens + output_tokens
        
        # Show session totals
        self._print_debug(f"📊 Session totals: ${self.total_cost:.6f} ({self.total_tokens:,} tokens)", Colors.TOKEN)
        
        # Project cost for 1000 calls
        if cost > 0:
            cost_per_1000 = cost * 1000
            print(f"{Colors.PURPLE}📈 Projected cost for 1000 similar PDF analysis requests: ${cost_per_1000:.2f}{Colors.RESET}")
    
    def _clean_logs(self):
        """Clean all log files from the .logs directory"""
        try:
            import shutil
            if self.logs_dir.exists():
                shutil.rmtree(self.logs_dir)
                self.logs_dir.mkdir(exist_ok=True)
                self._print_info("Logs directory cleaned", Colors.SUCCESS)
            else:
                self._print_info("Logs directory already clean", Colors.INFO)
        except Exception as e:
            self._print_error(f"Failed to clean logs: {str(e)}")
    
    def _is_question_relevant_to_document(self, question: str) -> bool:
        """Pre-check if question is relevant to the uploaded document"""
        if not self.document_topic and not self.document_summary:
            # First question - allow it (usually for initial summary/analysis)
            return True
            
        # Use a quick API call to classify relevance
        try:
            relevance_prompt = f"""
            Document topic/summary: {self.document_topic or self.document_summary or "PDF document"}
            
            User question: "{question}"
            
            Is this question directly related to the content of the document described above? 
            Answer only "YES" if the question requires information from the specific document.
            Answer "NO" if it's a general knowledge question, current events, or unrelated topic.
            
            Answer:"""
            
            relevance_model = self.config["models"]["relevance_checker"]
            response = self.client.chat.completions.create(
                model=relevance_model,
                messages=[{"role": "user", "content": relevance_prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            # Calculate cost for relevance check
            usage = response.usage
            relevance_cost = self._calculate_cost(relevance_model, usage.prompt_tokens, usage.completion_tokens)
            self._print_debug(f"💰 Relevance check cost: ${relevance_cost:.6f} ({relevance_model})", Colors.TOKEN)
            
            answer = response.choices[0].message.content.strip().upper()
            is_relevant = answer.startswith("YES")
            
            self._print_debug(f"Question relevance check: {answer} -> {'Relevant' if is_relevant else 'Not relevant'}", Colors.DEBUG)
            
            return is_relevant
            
        except Exception as e:
            self._print_debug(f"Relevance check failed: {e}", Colors.DEBUG)
            # On error, be conservative and allow the question
            return True
    
    def _log_context(self, context: Dict[str, Any]):
        """Log conversation context to markdown file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"context_{timestamp}.md"
        
        with open(log_file, 'w') as f:
            f.write(f"# Conversation Context Log\n\n")
            f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Model:** {context.get('model', 'Unknown')}\n\n")
            f.write(f"**Tools Used:** {', '.join(context.get('tools_used', []))}\n\n")
            f.write(f"**Token Usage:**\n")
            if 'usage' in context:
                usage = context['usage']
                f.write(f"- Prompt tokens: {usage.get('prompt_tokens', 0)}\n")
                f.write(f"- Completion tokens: {usage.get('completion_tokens', 0)}\n")
                f.write(f"- Total tokens: {usage.get('total_tokens', 0)}\n\n")
            
            f.write("## Messages Sent to Model\n\n")
            for i, msg in enumerate(context.get('messages', []), 1):
                role = msg.get('role', 'unknown')
                content = msg.get('content')
                f.write(f"### Message {i} ({role.title()})\n\n")
                if isinstance(content, str):
                    f.write(f"```\n{content}\n```\n\n")
                else:
                    f.write(f"```json\n{json.dumps(content, indent=2)}\n```\n\n")
            
            if 'response' in context:
                f.write("## Model Response\n\n")
                f.write(f"```json\n{json.dumps(context['response'], indent=2)}\n```\n\n")
    
    def analyze_pdf(self, file_path: str, question: str) -> str:
        """Analyze PDF using OpenAI Responses API with file search"""
        self._print_debug(f"Analyzing PDF: {file_path}", Colors.TOOL)
        self._print_debug(f"Question: {question}", Colors.TOOL)
        
        # Log file size information
        try:
            file_size = os.path.getsize(file_path)
            self._print_debug(f"PDF file size: {file_size:,} bytes ({file_size/1024:.1f} KB)", Colors.DEBUG)
        except Exception as e:
            self._print_debug(f"Could not get file size: {e}", Colors.DEBUG)
        
        try:
            # Upload file if not already uploaded
            if file_path not in self.uploaded_files:
                self._print_debug("Uploading file to OpenAI...", Colors.TOOL)
                with open(file_path, 'rb') as f:
                    file_obj = self.client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                self.uploaded_files[file_path] = file_obj.id
                self._print_debug(f"File uploaded with ID: {file_obj.id}", Colors.SUCCESS)
            
            # Create vector store if not already created for this file
            vector_store_key = f"{file_path}_vector_store"
            if vector_store_key not in self.uploaded_files:
                self._print_debug("Creating vector store...", Colors.TOOL)
                vector_store = self.client.vector_stores.create(name="PDF Analysis")
                self.uploaded_files[vector_store_key] = vector_store.id
                
                # Add file to vector store
                self._print_debug("Adding file to vector store...", Colors.TOOL)
                vector_store_file = self.client.vector_stores.files.create(
                    vector_store_id=vector_store.id,
                    file_id=self.uploaded_files[file_path]
                )
                
                # Wait for file processing
                self._print_debug("Waiting for file processing...", Colors.TOOL)
                import time
                max_wait = 30  # 30 seconds max wait
                waited = 0
                while waited < max_wait:
                    file_status = self.client.vector_stores.files.retrieve(
                        vector_store_id=vector_store.id,
                        file_id=self.uploaded_files[file_path]
                    )
                    if file_status.status == 'completed':
                        break
                    elif file_status.status == 'failed':
                        raise Exception(f"File processing failed: {file_status}")
                    time.sleep(1)
                    waited += 1
                
                if waited >= max_wait:
                    raise Exception("File processing timeout")
            else:
                vector_store_id = self.uploaded_files[vector_store_key]
                self._print_debug(f"Using existing vector store: {vector_store_id}", Colors.TOOL)
            
            # Use Responses API with file search
            self._print_debug("Using Responses API with file search...", Colors.TOOL)
            
            model = self.config["models"]["pdf_processor"]
            response = self.client.responses.create(
                model=model,
                input=question,
                instructions=self.config["openai"]["pdf_processor"]["system_prompt"],
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [self.uploaded_files[vector_store_key]]
                }]
            )
            
            self._print_debug("PDF analysis completed successfully", Colors.SUCCESS)
            
            # Log detailed token usage and cost for Responses API
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                input_tokens = getattr(usage, 'input_tokens', 0)
                output_tokens = getattr(usage, 'output_tokens', 0)
                total_tokens = getattr(usage, 'total_tokens', 0)
                
                self._print_debug(f"Responses API token breakdown:", Colors.TOKEN)
                self._print_debug(f"  - Input tokens: {input_tokens:,}", Colors.TOKEN)
                self._print_debug(f"  - Output tokens: {output_tokens:,}", Colors.TOKEN)
                self._print_debug(f"  - Total tokens: {total_tokens:,}", Colors.TOKEN)
                
                # Calculate and display cost
                cost = self._calculate_cost(model, input_tokens, output_tokens)
                self._print_cost_summary(model, input_tokens, output_tokens, cost)
                
                # Check for additional usage fields
                for attr in dir(usage):
                    if not attr.startswith('_') and 'token' in attr.lower():
                        value = getattr(usage, attr)
                        if value and attr not in ['input_tokens', 'output_tokens', 'total_tokens']:
                            self._print_debug(f"  - {attr}: {value}", Colors.TOKEN)
            else:
                self._print_debug("No usage information available from Responses API", Colors.DEBUG)
            
            # Extract response content from Responses API
            content_parts = []
            
            if hasattr(response, 'output') and response.output:
                # response.output is a list of items, look for ResponseOutputMessage items
                for item in response.output:
                    # Look for message items with content (type: ResponseOutputMessage)
                    if hasattr(item, 'content') and item.content:
                        for content_part in item.content:
                            if hasattr(content_part, 'text') and content_part.text:
                                content_parts.append(content_part.text)
            
            if content_parts:
                result = '\n'.join(content_parts)
                
                # Extract document topic from first analysis for future relevance checks
                if not self.document_topic and not self.document_summary:
                    # Extract a brief topic/summary for relevance checking
                    try:
                        topic_model = self.config["models"]["topic_extractor"]
                        topic_extraction = self.client.chat.completions.create(
                            model=topic_model,
                            messages=[{
                                "role": "user", 
                                "content": f"In 10 words or less, what is the main topic of this document summary:\n\n{result[:500]}..."
                            }],
                            temperature=0.1,
                            max_tokens=20
                        )
                        self.document_topic = topic_extraction.choices[0].message.content.strip()
                        
                        # Calculate cost for topic extraction
                        usage = topic_extraction.usage
                        topic_cost = self._calculate_cost(topic_model, usage.prompt_tokens, usage.completion_tokens)
                        self._print_debug(f"Document topic extracted: {self.document_topic}", Colors.DEBUG)
                        self._print_debug(f"💰 Topic extraction cost: ${topic_cost:.6f} ({topic_model})", Colors.TOKEN)
                    except Exception as e:
                        self._print_debug(f"Topic extraction failed: {e}", Colors.DEBUG)
                        self.document_topic = "PDF document content"
                
                return result
            else:
                # Try alternative extraction methods
                if hasattr(response, 'content'):
                    return response.content
                elif hasattr(response, 'choices') and response.choices:
                    return response.choices[0].message.content
                else:
                    return "No content could be extracted from the PDF analysis response."
                
        except Exception as e:
            self._print_error(f"Error analyzing PDF: {str(e)}")
            return f"Error analyzing PDF: {str(e)}"
    
    def _should_include_pdf_tool(self) -> tuple[bool, str]:
        """Determine if PDF tool should be included and with what choice"""
        if self.current_file_path is None:
            return False, "auto"
        
        if self.message_count_since_upload == 0:
            return True, "required"  # First message after upload (shouldn't happen with current logic)
        elif self.message_count_since_upload == 1:
            return True, "auto"  # First message gets auto (let relevance check and system prompt decide)
        elif self.message_count_since_upload <= 5:
            return True, "auto"  # Next 4 messages after first use, optional
        else:
            return False, "auto"  # After 5 messages total, don't include (unless reset by tool use)
    
    def _create_pdf_tool_definition(self) -> Dict:
        """Create the PDF analysis tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "analyze_pdf",
                "description": self.config["openai"]["pdf_processor"]["tool_description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": self.config["openai"]["pdf_processor"]["parameter_descriptions"]["file_path"]
                        },
                        "question": {
                            "type": "string",
                            "description": self.config["openai"]["pdf_processor"]["parameter_descriptions"]["question"]
                        },
                        "relevance_justification": {
                            "type": "string",
                            "description": self.config["openai"]["pdf_processor"]["parameter_descriptions"]["relevance_justification"]
                        }
                    },
                    "required": ["file_path", "question", "relevance_justification"]
                }
            }
        }
    
    def _update_system_prompt(self):
        """Update system prompt based on whether PDF tool is available"""
        include_tool, _ = self._should_include_pdf_tool()
        
        if include_tool:
            new_prompt = self.config["openai"]["main_agent"]["system_prompt_with_pdf"]
        else:
            new_prompt = self.config["openai"]["main_agent"]["system_prompt_base"]
        
        # Update the system message in conversation history
        self.conversation_history[0]["content"] = new_prompt
    
    def process_message(self, user_input: str) -> str:
        """Process user message and get AI response"""
        # Check for debugging flag
        force_no_file = "--no_file" in user_input
        if force_no_file:
            user_input = user_input.replace("--no_file", "").strip()
            self._print_debug("--no_file flag detected, disabling PDF tool", Colors.DEBUG)
        
        # Check if message contains file upload with question
        if "--file" in user_input:
            return self._handle_combined_message(user_input)
        
        # Update system prompt based on current context
        self._update_system_prompt()
        
        # Add user message to conversation
        self.conversation_history.append({
            "role": "user", 
            "content": user_input
        })
        
        # Determine tool configuration
        include_tool, tool_choice = self._should_include_pdf_tool()
        
        # Override tool inclusion if --no_file flag is used
        if force_no_file:
            include_tool = False
            self._print_debug("PDF tool disabled by --no_file flag", Colors.DEBUG)
        
        # Check question relevance if tool would be included
        if include_tool and tool_choice == "auto":
            is_relevant = self._is_question_relevant_to_document(user_input)
            if not is_relevant:
                include_tool = False
                self._print_debug("PDF tool disabled - question not relevant to document", Colors.DEBUG)
        
        tools = []
        tools_used = []
        
        if include_tool:
            tools.append(self._create_pdf_tool_definition())
            self._print_debug(f"PDF tool included with choice: {tool_choice}", Colors.TOOL)
        else:
            self._print_debug("No PDF tool included", Colors.DEBUG)
        
        model = self.config["models"]["main_agent"]
        self._print_debug(f"Using model: {model}", Colors.DEBUG)
        
        try:
            # Prepare API call parameters
            api_params = {
                "model": model,
                "messages": self.conversation_history,
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            if tools:
                api_params["tools"] = tools
                if tool_choice == "required":
                    api_params["tool_choice"] = "required"
            
            # Make API call
            response = self.client.chat.completions.create(**api_params)
            
            # Log token usage and cost
            usage = response.usage
            self._print_debug(
                f"Token usage - Prompt: {usage.prompt_tokens}, "
                f"Completion: {usage.completion_tokens}, "
                f"Total: {usage.total_tokens}",
                Colors.TOKEN
            )
            
            # Calculate and display cost for main chat
            cost = self._calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)
            if cost > 0:
                self._print_debug(f"💰 Main chat cost: ${cost:.6f}", Colors.TOKEN)
            
            message = response.choices[0].message
            
            # Handle tool calls
            if message.tool_calls:
                self._print_debug("Model requested tool execution", Colors.TOOL)
                tools_used.append("analyze_pdf")
                
                # Add assistant message with tool calls
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls]
                })
                
                # Execute tool calls
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "analyze_pdf":
                        args = json.loads(tool_call.function.arguments)
                        # Always use the current uploaded file path
                        file_path = self.current_file_path if self.current_file_path else args.get("file_path", "")
                        question = args.get("question", user_input)
                        justification = args.get("relevance_justification", "")
                        
                        # Log the justification
                        if justification:
                            self._print_debug(f"Tool justification: {justification}", Colors.TOOL)
                        
                        result = self.analyze_pdf(file_path, question)
                        
                        # Add tool response
                        self.conversation_history.append({
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call.id
                        })
                
                # Get final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=model,
                    messages=self.conversation_history,
                    temperature=0.7,
                    max_tokens=1500
                )
                
                final_message = final_response.choices[0].message
                assistant_response = final_message.content
                
                # Update token usage
                usage = final_response.usage
                self._print_debug(
                    f"Final token usage - Prompt: {usage.prompt_tokens}, "
                    f"Completion: {usage.completion_tokens}, "
                    f"Total: {usage.total_tokens}",
                    Colors.TOKEN
                )
            else:
                assistant_response = message.content
            
            # Add assistant response to conversation
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # Log context
            context = {
                "model": model,
                "tools_used": tools_used,
                "usage": usage.model_dump(),
                "messages": self.conversation_history[-3:],  # Last few messages
                "response": assistant_response
            }
            self._log_context(context)
            
            # Handle message count - reset if PDF tool was used, otherwise increment
            if self.current_file_path:
                if "analyze_pdf" in tools_used:
                    # Reset counter when PDF tool is actively used
                    self.message_count_since_upload = 1
                    self._print_debug(f"Message count reset to 1 (PDF tool used)", Colors.DEBUG)
                else:
                    # Normal increment when tool not used
                    self.message_count_since_upload += 1
                    self._print_debug(f"Message count since upload: {self.message_count_since_upload}", Colors.DEBUG)
            
            return assistant_response
            
        except Exception as e:
            self._print_error(f"Error processing message: {str(e)}")
            return f"I encountered an error: {str(e)}"
    
    def _handle_file_upload(self, command: str) -> str:
        """Handle file upload command"""
        parts = command.split()
        if len(parts) != 2:
            return "Usage: --file <path_to_pdf>"
        
        file_path = parts[1]
        
        # Convert to absolute path for better handling
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Check if file exists and is accessible
        if not os.path.exists(file_path):
            return f"File not found: {file_path}\nMake sure the path is correct and the file exists."
        
        if not file_path.lower().endswith('.pdf'):
            return "Only PDF files are supported"
        
        self.current_file_path = file_path
        self.message_count_since_upload = 0
        
        self._print_info(f"PDF uploaded: {file_path}", Colors.SUCCESS)
        self._print_debug("PDF tool will be required for next message", Colors.TOOL)
        
        return f"PDF file '{os.path.basename(file_path)}' has been uploaded successfully. You can now ask questions about the document."
    
    def _handle_combined_message(self, user_input: str) -> str:
        """Handle message that contains both a question and file upload"""
        # Parse the message to extract question and file path
        parts = user_input.split("--file")
        if len(parts) != 2:
            return "Usage: <question> --file <path_to_pdf>"
        
        question = parts[0].strip()
        file_arg = parts[1].strip()
        
        if not question:
            return "Please provide a question before --file parameter"
        
        # Handle file upload first
        file_path = file_arg
        
        # Convert to absolute path for better handling
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Check if file exists and is accessible
        if not os.path.exists(file_path):
            return f"File not found: {file_path}\nMake sure the path is correct and the file exists."
        
        if not file_path.lower().endswith('.pdf'):
            return "Only PDF files are supported"
        
        # Set up file context
        self.current_file_path = file_path
        self.message_count_since_upload = 0
        
        self._print_info(f"PDF uploaded: {file_path}", Colors.SUCCESS)
        self._print_debug("Processing combined message with file upload", Colors.TOOL)
        
        # Update system prompt to include PDF tool instructions
        self._update_system_prompt()
        
        # Add user message to conversation
        self.conversation_history.append({
            "role": "user", 
            "content": question
        })
        
        # Force tool usage for combined upload+question message
        tools = [self._create_pdf_tool_definition()]
        tools_used = []
        tool_choice = "required"
        
        self._print_debug("PDF tool included with choice: required (combined upload)", Colors.TOOL)
        
        model = self.config["models"]["main_agent"]
        self._print_debug(f"Using model: {model}", Colors.DEBUG)
        
        try:
            # Prepare API call parameters with required tool
            api_params = {
                "model": model,
                "messages": self.conversation_history,
                "temperature": 0.7,
                "max_tokens": 1500,
                "tools": tools,
                "tool_choice": "required"
            }
            
            # Make API call
            response = self.client.chat.completions.create(**api_params)
            
            # Log token usage and cost
            usage = response.usage
            self._print_debug(
                f"Token usage - Prompt: {usage.prompt_tokens}, "
                f"Completion: {usage.completion_tokens}, "
                f"Total: {usage.total_tokens}",
                Colors.TOKEN
            )
            
            # Calculate and display cost for main chat
            cost = self._calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)
            if cost > 0:
                self._print_debug(f"💰 Main chat cost: ${cost:.6f}", Colors.TOKEN)
            
            message = response.choices[0].message
            
            # Handle tool calls (should always have them since we forced it)
            if message.tool_calls:
                self._print_debug("Model requested tool execution", Colors.TOOL)
                tools_used.append("analyze_pdf")
                
                # Add assistant message with tool calls
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls]
                })
                
                # Execute tool calls
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "analyze_pdf":
                        args = json.loads(tool_call.function.arguments)
                        # Use the current file path and the user's question
                        justification = args.get("relevance_justification", "")
                        
                        # Log the justification
                        if justification:
                            self._print_debug(f"Tool justification: {justification}", Colors.TOOL)
                        
                        result = self.analyze_pdf(self.current_file_path, question)
                        
                        # Add tool response
                        self.conversation_history.append({
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call.id
                        })
                
                # Get final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=model,
                    messages=self.conversation_history,
                    temperature=0.7,
                    max_tokens=1500
                )
                
                final_message = final_response.choices[0].message
                assistant_response = final_message.content
                
                # Update token usage
                usage = final_response.usage
                self._print_debug(
                    f"Final token usage - Prompt: {usage.prompt_tokens}, "
                    f"Completion: {usage.completion_tokens}, "
                    f"Total: {usage.total_tokens}",
                    Colors.TOKEN
                )
            else:
                assistant_response = message.content
            
            # Add assistant response to conversation
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # Log context
            context = {
                "model": model,
                "tools_used": tools_used,
                "usage": usage.model_dump(),
                "messages": self.conversation_history[-3:],  # Last few messages
                "response": assistant_response
            }
            self._log_context(context)
            
            # Set message count to 1 for combined upload+question
            self.message_count_since_upload = 1
            self._print_debug(f"Message count set to 1 (combined upload+question)", Colors.DEBUG)
            
            return assistant_response
            
        except Exception as e:
            self._print_error(f"Error processing combined message: {str(e)}")
            return f"I encountered an error: {str(e)}"
    
    def run(self):
        """Run the interactive CLI"""
        print(f"{Colors.SUCCESS}PDF Document Analysis CLI{Colors.RESET}")
        print(f"{Colors.INFO}Upload a PDF with: --file <path>{Colors.RESET}")
        print(f"{Colors.INFO}Disable PDF tool with: --no_file (for debugging){Colors.RESET}")
        print(f"{Colors.INFO}Type 'quit' or 'exit' to end the session{Colors.RESET}")
        print(f"{Colors.DEBUG}Debug info will be shown in {Colors.DEBUG}magenta{Colors.RESET}")
        print(f"{Colors.TOOL}Tool usage will be shown in {Colors.TOOL}yellow{Colors.RESET}")
        print(f"{Colors.TOKEN}Token usage will be shown in {Colors.TOKEN}gray{Colors.RESET}")
        print("-" * 60)
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n{Colors.USER}You: {Colors.RESET}").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    print(f"{Colors.INFO}Goodbye!{Colors.RESET}")
                    break
                
                if not user_input:
                    continue
                
                # Process and display response
                response = self.process_message(user_input)
                print(f"\n{Colors.ASSISTANT}Assistant: {Colors.RESET}{response}")
                
            except KeyboardInterrupt:
                print(f"\n{Colors.INFO}Session interrupted. Goodbye!{Colors.RESET}")
                break
            except EOFError:
                print(f"\n{Colors.INFO}Session ended. Goodbye!{Colors.RESET}")
                break
            except Exception as e:
                self._print_error(f"Unexpected error: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="PDF Document Analysis CLI")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--clean", action="store_true", help="Clean logs directory on startup")
    args = parser.parse_args()
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print(f"{Colors.ERROR}OPENAI_API_KEY environment variable not set{Colors.RESET}")
        print(f"{Colors.INFO}Make sure you have a .env file with OPENAI_API_KEY=your-key{Colors.RESET}")
        sys.exit(1)
    
    # Initialize and run CLI
    cli = PDFChatCLI(args.config, clean_logs=args.clean)
    cli.run()

if __name__ == "__main__":
    main()