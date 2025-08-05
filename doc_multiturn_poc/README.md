# PDF Document Analysis CLI - Multi-turn Conversation PoC

A proof-of-concept CLI application that demonstrates multi-turn conversations with PDF document analysis using OpenAI's new responses API and file_search tool.

## Features

- Interactive CLI chat interface with color-coded debug information
- PDF document upload and analysis using OpenAI file_search
- Multi-turn conversation support with context retention
- Smart tool injection logic (required first use, optional for next 5 messages)
- Comprehensive logging of conversation context
- Configurable system prompts and tool descriptions

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

3. Run the CLI:
```bash
python chat_cli.py
```

## Usage

1. **Start a conversation**: Simply type your message after starting the CLI
2. **Upload a PDF**: Use `--file <path_to_pdf>` to upload a document
3. **Ask questions**: After uploading, ask questions about the document
4. **Continue chatting**: The tool will be available for the next 5 messages automatically

## Example Session

```
PDF Document Analysis CLI
Upload a PDF with: --file <path>
Type 'quit' or 'exit' to end the session

You: --file media/clevertap.pdf
Assistant: PDF file 'media/clevertap.pdf' has been uploaded successfully. You can now ask questions about the document.

You: What is this document about?
[DEBUG] Using model: gpt-4o-mini
[DEBUG] PDF tool included with choice: required
[DEBUG] Model requested tool execution
[DEBUG] Analyzing PDF: media/clevertap.pdf
[DEBUG] Token usage - Prompt: 450, Completion: 120, Total: 570