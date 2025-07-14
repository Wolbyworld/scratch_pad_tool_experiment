# Scratch Pad AI Tool

A personal knowledge assistant that processes queries by loading and analyzing a local scratch pad document to provide relevant contextual responses using OpenAI's GPT models.

## Features

- **Intelligent Context Extraction**: Uses AI to find relevant information from your personal knowledge base
- **Enhanced Media Processing**: Two-stage approach to determine if visual analysis is needed
- **CLI Interface**: Simple command-line tool for quick queries
- **Configurable**: Easily editable system prompts and flexible file paths
- **Multi-user Ready**: Parameterized file paths for future multi-user support

## Project Structure

```
scratch_pad_tool/
├── .env                    # API key configuration (create from .env.template)
├── config/
│   └── system_prompt.txt   # Editable system prompt
├── media/                  # Media files referenced in scratch pad
│   ├── dni.png            # Example: ID document
│   └── gorilla.png        # Example: Artwork
├── scratchpad.py          # Main tool executable
├── scratchpad.txt         # Your personal scratch pad document
├── requirements.txt       # Python dependencies
├── .env.template          # Template for environment configuration
└── README.md             # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ```

### 3. Customize Your Scratch Pad

Edit `scratchpad.txt` with your personal information:

- **MEDIA DOCUMENTS**: Add file paths, descriptions, and summaries of your images/PDFs
- **USER FACTS**: Add personal information, preferences, current projects, etc.

### 4. Customize System Prompt (Optional)

Edit `config/system_prompt.txt` to modify how the AI processes and responds to your queries.

## Usage

### Basic Usage

```bash
python scratchpad.py "What are my current AI projects?"
```

### Advanced Options

```bash
# Use custom scratch pad file
python scratchpad.py -f my_other_scratchpad.txt "What's my age?"

# Use custom system prompt
python scratchpad.py -p custom_prompt.txt "Tell me about my artwork"

# Verbose mode (shows processing details)
python scratchpad.py -v "What's my date of birth?"
```

### Example Queries

- `"What are my current projects?"`
- `"What's my date of birth?"`
- `"Tell me about the gorilla artwork"`
- `"What programming languages do I prefer?"`
- `"Show me my personal information"`

## How It Works

### Two-Stage Processing

1. **Stage 1 - Media Assessment**: The AI determines if any media files are necessary to answer your query and whether visual analysis is needed
2. **Stage 2 - Context Extraction**: The AI extracts the most relevant information from your scratch pad using the enhanced system prompt

### Enhanced Media Processing

When you ask about media content, the tool:
- Determines if media files are necessary for your query
- Assesses whether existing text summaries are sufficient
- Indicates when detailed visual analysis would be beneficial
- Provides structured responses with clear reasoning

## Configuration Files

### System Prompt (`config/system_prompt.txt`)

Customize how the AI processes your queries. The default prompt includes:
- Enhanced media processing instructions
- Output formatting guidelines
- Context extraction strategies

### Environment Variables (`.env`)

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `SCRATCHPAD_FILE`: Default scratch pad file path (optional)
- `SYSTEM_PROMPT_FILE`: Default system prompt file path (optional)

## Error Handling

The tool follows the KISS (Keep It Simple, Stupid) principle for error handling:

- **Missing API key**: Clear error message with setup instructions
- **Missing scratch pad**: Helpful error indicating file not found
- **API errors**: Simple error messages without exposing technical details
- **Malformed queries**: Graceful handling with fallback responses

## Future Enhancements

- Multi-user support (file paths are already parameterized)
- Visual analysis integration for detailed image processing
- Web interface option
- Integration with other productivity tools

## License

This project is for personal use and experimentation with AI-powered productivity tools.

## Contributing

This is a personal productivity tool, but suggestions and improvements are welcome! 