# Luzia Chat Web Interface

A beautiful, modern ChatGPT-style web interface for the Luzia chat system with integrated scratchpad editing.

## Features

- **Modern ChatGPT-style interface**: Clean, beautiful chat interface with animated message bubbles
- **Visual separation**: Clear distinction between AI responses and debugging information
- **Editable scratchpad sidebar**: Real-time editing and saving of your scratchpad
- **Integrated AI tools**: Automatic scratchpad context integration and media analysis
- **Enhanced UX**: Smooth animations, typing indicators, and modern gradients
- **Session management**: Each browser session gets its own conversation history
- **Responsive design**: Works beautifully on desktop and mobile devices

## Visual Improvements

### Message Design
- **Bubble layout**: Modern message bubbles with rounded corners and shadows
- **Gradient avatars**: Beautiful gradient backgrounds for user and assistant avatars
- **Smooth animations**: Messages slide in with elegant animations
- **Typography**: Clean, readable fonts with proper spacing

### Debug Information
- **Separated debug info**: Debug information appears in a distinct section below messages
- **Color-coded badges**: Visual indicators for different types of AI tools used
- **Compact display**: Debug info is visually separate but doesn't clutter the conversation

### Interface Polish
- **Gradient backgrounds**: Beautiful purple-to-blue gradient background
- **Glass morphism**: Semi-transparent panels with backdrop blur effects
- **Improved spacing**: Better padding and margins throughout
- **Hover effects**: Subtle animations on buttons and interactive elements
- **Typing indicator**: Animated dots when Luzia is thinking

## Setup

1. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   # Edit the .env file
   nano .env
   # Add your OpenAI API key:
   OPENAI_API_KEY=your_openai_api_key_here
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
- Type your message in the rounded input field at the bottom
- Press Enter or click the gradient Send button
- Watch the typing indicator while Luzia processes your message
- Messages appear in beautiful bubbles with smooth animations
- Debug information appears in a separate section below AI responses

### Debug Information
- **Tools Used**: Shows which AI tools were called (e.g., get_scratch_pad_context)
- **Context Status**: Indicates when scratchpad context was retrieved
- **Media Analysis**: Shows when media files were analyzed
- **Error Handling**: Clear error indicators if something goes wrong

### Scratchpad Editing
- The right sidebar shows your scratchpad content in a monospace font
- Edit the text directly in the textarea with syntax highlighting
- Click the gradient "Save" button to save changes
- Click "Reload" to refresh the current file content
- Status messages show save/load progress with color coding

### Enhanced Features
- **Smooth scrolling**: Auto-scroll to new messages
- **Keyboard shortcuts**: Ctrl+S to save scratchpad
- **Responsive design**: Adapts beautifully to different screen sizes
- **Visual feedback**: Buttons respond to hover and clicks
- **Loading states**: Clear indicators when operations are in progress

## Design System

### Colors
- **Primary Gradient**: Purple to blue (#667eea to #764ba2)
- **Secondary Gradient**: Green tones (#10b981 to #059669)
- **Backgrounds**: Glass morphism with blur effects
- **Text**: High contrast grays for readability

### Typography
- **Main Font**: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI)
- **Code Font**: Monospace for scratchpad (SF Mono, Monaco, Consolas)
- **Sizes**: Responsive scaling from 0.75rem to 2rem

### Animations
- **Message Entry**: Slide up with fade in (0.3s ease-out)
- **Typing Indicator**: Bouncing dots animation
- **Buttons**: Subtle lift on hover
- **Smooth Transitions**: 0.2s duration for all interactive elements

## Technical Implementation

### Backend (Flask)
- **Structured responses**: Messages and debug info are separated
- **Error handling**: Graceful error messages with context
- **Session management**: In-memory conversation storage
- **API endpoints**: RESTful design for chat and scratchpad operations

### Frontend (Vanilla JS)
- **Modern JavaScript**: ES6+ features with clean code
- **No frameworks**: Lightweight vanilla JavaScript for performance
- **Responsive design**: CSS Grid and Flexbox for layout
- **Accessibility**: Proper ARIA labels and keyboard navigation

### Data Flow
1. User types message → Frontend validates and sends to `/chat`
2. Backend calls Luzia with function tools → Returns structured response
3. Frontend receives message + debug info → Renders in separate sections
4. Debug info appears in dedicated area below main message

## Browser Support

- **Chrome/Chromium**: Full support (recommended)
- **Firefox**: Full support
- **Safari**: Full support with backdrop-filter
- **Edge**: Full support

## Development

To modify the interface:

1. **Styling**: Edit the `<style>` section in `templates/index.html`
2. **Functionality**: Modify the JavaScript in the same file
3. **Backend**: Update `app.py` for API changes
4. **Restart**: The Flask app to see changes (auto-reload in debug mode)

## Troubleshooting

**Styling issues:**
- Check browser console for CSS errors
- Verify backdrop-filter support in older browsers
- Test responsive design on different screen sizes

**Debug info not showing:**
- Verify the Flask app is returning `debug_info` in responses
- Check browser console for JavaScript errors
- Ensure OpenAI API calls are successful

**Performance issues:**
- Monitor memory usage for long conversations
- Consider clearing chat history periodically
- Check for JavaScript memory leaks in dev tools

## Customization

### Colors
Edit the CSS custom properties in `templates/index.html`:
- Change gradient colors in `linear-gradient()` declarations
- Modify shadow colors in `box-shadow` properties
- Update text colors in color declarations

### Animations
Adjust animation timing in CSS:
- `animation-duration` for typing dots
- `transition` properties for hover effects
- `@keyframes` for custom animations

### Layout
Modify layout in CSS:
- Adjust container widths and heights
- Change spacing with `padding` and `margin`
- Update responsive breakpoints in media queries