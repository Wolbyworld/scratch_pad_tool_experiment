# Luzia Chat Web Interface

A simple ChatGPT-style web interface for the Luzia chat system with integrated scratchpad editing.

## Features

- **ChatGPT-style interface**: Clean, modern chat interface with message bubbles
- **Editable scratchpad sidebar**: Real-time editing and saving of your scratchpad
- **Integrated AI tools**: Automatic scratchpad context integration and media analysis
- **Session management**: Each browser session gets its own conversation history
- **Responsive design**: Works on desktop and mobile devices

## Setup

1. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   # Copy and edit the .env file
   cp .env.example .env
   # Add your OpenAI API key
   ```

3. **Start the web interface:**
   ```bash
   # Option 1: Use the start script
   ./start_web.sh
   
   # Option 2: Manual start
   source venv/bin/activate
   python app.py
   ```

4. **Open in browser:**
   - Navigate to `http://localhost:5000`

## Usage

### Chat Interface
- Type your message in the input field at the bottom
- Press Enter or click Send to send your message
- Luzia will automatically access your scratchpad for context
- Messages appear in chat bubbles with user messages on the right and Luzia's responses on the left

### Scratchpad Editing
- The right sidebar shows your scratchpad content
- Edit the text directly in the textarea
- Click "Save" to save changes to `scratchpad.txt`
- Click "Reload" to reload the current file content
- Status messages show save/load progress

### Features
- **Auto-context**: Every message automatically gets relevant context from your scratchpad
- **Media analysis**: If your scratchpad mentions media files, Luzia can analyze them
- **Session memory**: Each browser session maintains its own conversation history
- **Responsive design**: Works on mobile and desktop

## Files

- `app.py` - Main Flask application
- `templates/index.html` - Web interface HTML template
- `tools.py` - Scratchpad and media analysis tools
- `scratchpad.txt` - Your personal scratchpad file
- `config/` - Configuration files and system prompts
- `media/` - Media files referenced in scratchpad

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **AI**: OpenAI GPT-4 with function calling
- **Tools**: Scratchpad context extraction, media analysis

## API Endpoints

- `GET /` - Main web interface
- `POST /chat` - Send message to chat system
- `GET /scratchpad` - Load scratchpad content
- `POST /scratchpad` - Save scratchpad content

## Keyboard Shortcuts

- **Enter**: Send message
- **Shift+Enter**: New line in message input
- **Ctrl+S**: Save scratchpad (when focused on scratchpad)

## Browser Support

- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge

## Development

To modify the interface:
1. Edit `templates/index.html` for HTML/CSS/JavaScript changes
2. Edit `app.py` for backend logic changes
3. Restart the Flask app to see changes

## Troubleshooting

**App won't start:**
- Check that your virtual environment is activated
- Verify OpenAI API key is set in `.env` file
- Ensure port 5000 is available

**Chat not working:**
- Check browser console for JavaScript errors
- Verify OpenAI API key is valid
- Check Flask app logs for error messages

**Scratchpad not saving:**
- Check file permissions in the project directory
- Verify the scratchpad.txt file exists and is writable