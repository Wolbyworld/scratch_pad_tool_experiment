from flask import Flask, render_template, request, jsonify, session
from tools import ScratchPadTools
import openai
import os
import json
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Load OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Initialize tools
tools = ScratchPadTools()

# Store conversations in memory (simple approach)
conversations = {}

@app.route('/')
def index():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = session.get('session_id')
    
    if session_id not in conversations:
        conversations[session_id] = []
    
    # Add user message to conversation
    conversations[session_id].append({
        "role": "user",
        "content": user_message
    })
    
    try:
        # Get response from Luzia (reuse existing logic)
        response = get_luzia_response(user_message, conversations[session_id])
        
        # Add AI response to conversation
        conversations[session_id].append({
            "role": "assistant", 
            "content": response
        })
        
        return jsonify({
            "response": response,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "response": f"Error: {str(e)}",
            "status": "error"
        })

@app.route('/scratchpad', methods=['GET'])
def get_scratchpad():
    try:
        with open('scratchpad.txt', 'r') as f:
            content = f.read()
        return jsonify({
            "content": content,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "content": f"Error loading scratchpad: {str(e)}",
            "status": "error"
        })

@app.route('/scratchpad', methods=['POST'])
def save_scratchpad():
    data = request.json
    content = data.get('content', '')
    
    try:
        with open('scratchpad.txt', 'w') as f:
            f.write(content)
        return jsonify({
            "status": "success",
            "message": "Scratchpad saved successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error saving scratchpad: {str(e)}"
        })

def get_luzia_response(user_message, conversation_history):
    """Reuse Luzia logic from existing system"""
    
    # Load system prompt
    with open('config/system_prompt.txt', 'r') as f:
        system_prompt = f.read()
    
    # Prepare function tools
    function_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_scratch_pad_context",
                "description": "Get relevant context from the user's scratch pad document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The user's query to find relevant context for"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_media_file",
                "description": "Analyze a media file (image) when the scratch pad indicates it's needed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the media file to analyze"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
    ]
    
    # Prepare messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    
    # Call OpenAI
    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        tools=function_tools,
        tool_choice={"type": "function", "function": {"name": "get_scratch_pad_context"}}
    )
    
    # Handle function calls
    if response.choices[0].message.tool_calls:
        # Process tool calls
        messages.append(response.choices[0].message)
        
        for tool_call in response.choices[0].message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "get_scratch_pad_context":
                result = tools.get_scratch_pad_context(function_args["query"])
            elif function_name == "analyze_media_file":
                result = tools.analyze_media_file(function_args["file_path"])
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(result)
            })
        
        # Get final response
        final_response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages
        )
        
        return final_response.choices[0].message.content
    
    return response.choices[0].message.content

if __name__ == '__main__':
    app.run(debug=True, port=5000)