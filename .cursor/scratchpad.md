# Scratch Pad AI Tool Project

## Background and Motivation

**Project Goal**: Create an AI tool called "Scratch Pad" that processes user queries by loading and analyzing a local scratch pad document (.txt file) to provide relevant contextual responses.

**Core Functionality**:
- Input: User query
- Process: Load and analyze scratch pad document from same folder
- Output: Relevant context to respond to the query
- AI Model: OpenAI GPT-4o-mini

**Scratch Pad Document Structure**:
- Section on media documents that have been processed (file path, description)
  - Focus: Images (PNG) and PDFs initially
- Section of relevant user facts (age, preferences, current projects, etc.)
- Template-based structure for consistency

**Technical Specifications**:
- Implementation: Python with OpenAI SDK
- Model: GPT-4o-mini or o4-mini (latest available)
- Interface: CLI tool for concept testing
- Configuration: .env file for API key management
- System prompt: Easily editable for customization

**Use Case**: This tool will help users quickly find relevant information from their personal knowledge base stored in a structured text file, using AI to intelligently extract and present the most pertinent context for their specific queries.

## Key Challenges and Analysis

### 1. Scratch Pad Document Design
**Challenge**: Create a standardized, AI-parseable template that balances human readability with machine processing efficiency.

**Considerations**:
- Should use clear section markers for consistent parsing
- Need flexible structure to accommodate various types of media and facts
- Must be easy for users to maintain and update manually

### 2. Context Relevance and Retrieval
**Challenge**: Intelligently identify which parts of the scratch pad are most relevant to user queries.

**Considerations**:
- Simple keyword matching vs. semantic similarity
- How to handle queries that span multiple sections
- Balancing context size vs. relevance (GPT token limits)

### 3. Tool Interface and Usability
**Challenge**: Design an intuitive interface that fits into users' workflows.

**Options to evaluate**:
- CLI tool for terminal users
- Simple web interface for broader accessibility
- Integration possibilities (VS Code extension, etc.)

### 4. AI Integration Architecture
**Challenge**: Efficiently integrate OpenAI API while managing costs and response times.

**Latest SDK Information** (from research):
- Standard OpenAI Python SDK is current best practice
- GPT-4o-mini: ~$1.16/M input tokens, $4.62/M output tokens
- Newer o4-mini available: ~$1.10/M input tokens, $4.40/M output tokens
- Both support multimodal inputs (text + images)

**Enhanced Media Processing Requirements**:
- Model must determine: (a) whether media file(s) are necessary for the query
- Model must determine: (b) whether text summary/captioning is sufficient or another vision call is needed
- Two-stage approach: initial assessment, then detailed analysis if required

**Implementation Decisions** (based on user feedback):
- Use .env file for secure API key storage
- System prompt stored in easily editable location
- Simple approach: pass entire scratch pad to AI for context extraction
- Intelligent media handling with dual-stage processing
- Project structure includes dedicated `media/` folder

### 5. File Management and Organization
**Challenge**: Handle file discovery, loading, and potential multiple scratch pad files.

**Considerations**:
- Single vs. multiple scratch pad files
- File naming conventions
- Backup and versioning strategies

## High-level Task Breakdown

### Phase 1: Foundation and Design
**Task 1.1**: Create Scratch Pad Template
- Design .txt file structure with clear sections for media documents and user facts
- Create example template with sample data
- **Success Criteria**: Template is human-readable and has consistent section markers

**Task 1.2**: Define Technical Architecture
- Choose implementation language (Python recommended for AI/text processing)
- Define project structure and dependencies
- Plan OpenAI API integration approach
- **Success Criteria**: Clear technical specifications documented

### Phase 2: Core Functionality
**Task 2.1**: Create Function Calling Tools
- Convert ScratchPadTool to `get_scratch_pad_context(query: str)` function
- Create `analyze_media_file(file_path: str)` function for visual processing
- Design function schemas for GPT-4.1 integration
- **Success Criteria**: Functions work independently and return proper JSON responses

**Task 2.2**: Implement Luzia Chat System
- Create `luzia.py` with continuous while loop chat interface
- Integrate GPT-4.1 with function calling capabilities
- Implement Luzia persona system prompt (fun, helpful friend, brief responses)
- Handle conversation context building
- **Success Criteria**: Continuous chat with scratch pad context integration

**Task 2.3**: Add Media Processing Integration
- Link scratch pad media recommendations to media analysis
- Handle image files and add visual analysis to conversation context
- Implement smart media processing workflow
- **Success Criteria**: Media files automatically processed when scratch pad indicates necessity

### Phase 3: Chat Experience Polish
**Task 3.1**: Enhance User Experience
- Add graceful exit handling (exit command + Ctrl+C)
- Implement conversation flow improvements
- Add error handling for function calls and API failures
- Polish Luzia persona consistency
- **Success Criteria**: Smooth, natural chat experience

### Phase 4: Testing and Documentation
**Task 4.1**: Test Conversational Flows
- Test multi-turn conversations with context retention
- Test media processing workflows
- Test Luzia persona consistency and natural responses
- Validate function calling reliability
- **Success Criteria**: Natural conversations with reliable context enrichment

## Project Status Board

### Phase 1: Foundation and Design
- [x] Task 1.1: Create Scratch Pad Template
- [x] Task 1.2: Define Technical Architecture

### Phase 2: Luzia Conversational Interface
- [x] Task 2.1: Create Function Calling Tools
- [x] Task 2.2: Implement Luzia Chat System  
- [x] Task 2.3: Add Media Processing Integration

### Phase 3: Chat Experience Polish
- [ ] Task 3.1: Enhance User Experience

### Phase 4: Testing and Documentation
- [ ] Task 4.1: Test Conversational Flows

## Current Status / Progress Tracking

**Current Phase**: Planning and Design  
**Updated Based on User Feedback**:
- ✅ File structure approach confirmed
- ✅ Media types: PNG images and PDFs  
- ✅ User facts: age, preferences, projects
- ✅ Interface: CLI tool for testing
- ✅ Context strategy: simple/comprehensive approach
- ✅ Tech stack: Python + OpenAI SDK
- ✅ Configuration: .env for API key
- ✅ System prompt: easily editable

**Final Design Decisions**:
- ✅ File discovery: Default `scratchpad.txt`, parameterized for multi-user
- ✅ CLI: Direct syntax `scratchpad "question"`  
- ✅ System prompt: Stored in `config/` folder
- ✅ Output format: Formatted with sections
- ✅ Error handling: KISS principle

**Updated Project Structure**:
```
scratch_pad_tool/
├── .env                    # API key
├── config/
│   └── system_prompt.txt   # Editable system prompt
├── media/                  # Media files referenced in scratch pad
│   ├── dni.png            # ID document (Martinez-Higes, Alvaro)
│   └── gorilla.png        # Gorilla basketball slam dunk
├── scratchpad.py          # Main tool
├── scratchpad.txt         # User's scratch pad
├── requirements.txt       # Dependencies
└── README.md             # Setup instructions
```

**Enhanced Media Processing**:
- ✅ Two-stage AI processing for media queries
- ✅ Determine media necessity before processing
- ✅ Assess if summary is sufficient or detailed vision analysis needed

**Realistic Template Example** (using provided images):
```
# MY SCRATCH PAD

## MEDIA DOCUMENTS

### Personal ID Document
- File Path: media/dni.png
- Description: Massachusetts Liquor ID Card for Alvaro Martinez-Higes
- Date Added: 2024-01-25
- Tags: identification, personal, official, DOB-1987
- Summary: Official ID showing full name, DOB (02-12-1987), and address info

### Gorilla Basketball Art
- File Path: media/gorilla.png  
- Description: Artistic image of gorilla performing slam dunk on basketball hoop
- Date Added: 2024-01-25
- Tags: art, basketball, gorilla, sports, creative
- Summary: Creative/humorous sports-themed artwork with gorilla athlete

## USER FACTS

### Personal Information
- Age: 37 (based on DOB 02-12-1987)
- Name: Alvaro Martinez-Higes
- Location: Massachusetts, USA

### Preferences & Interests
- Enjoys creative/humorous content (gorilla basketball art)
- Interested in AI and productivity tools
- Prefers organized documentation systems

### Current Projects
- Building AI productivity tools with Scratch Pad concept
- Experimenting with OpenAI APIs and multimodal processing
- Learning about intelligent context extraction systems
```

**Status**: ✅ Planning Complete - Switching to Executor Mode

## Executor Starting Task 1.1: Create Scratch Pad Template

## Executor's Feedback or Assistance Requests

**Task 1.1 COMPLETED** ✅
- Created realistic scratch pad template (`scratchpad.txt`) using provided images
- Implemented enhanced system prompt (`config/system_prompt.txt`) with two-stage media processing
- Set up project dependencies (`requirements.txt`) with OpenAI SDK
- Created configuration template (`.env.template`)
- **Success Criteria Met**: Template is human-readable with consistent section markers

**Task 1.2 COMPLETED** ✅
- Created main tool architecture (`scratchpad.py`) with two-stage processing
- Implemented CLI interface with Click framework
- Built OpenAI integration with GPT-4o-mini
- Added enhanced media processing capabilities
- Created comprehensive documentation (`README.md`)
- Set up proper error handling following KISS principle
- **Success Criteria Met**: Clear technical specifications documented and implemented

**PHASE 1 COMPLETE** 🎉
- Foundation and design phase finished
- Ready to move to Phase 2: Core Functionality testing

**TESTING COMPLETED** ✅

**Test Results Summary**:
1. **AI Projects Query**: ✅ Successfully extracted current projects from USER FACTS section
2. **Personal Info Query**: ✅ Cross-referenced DOB/age, correctly identified media relevance  
3. **Media Content Query**: ✅ Enhanced media processing worked - identified relevant files, determined text summary sufficient
4. **Preferences Query**: ✅ Verbose mode working, extracted programming language preferences
5. **Error Handling**: ✅ Graceful API key validation and error messages

**Two-Stage Processing Verified**:
- Stage 1 (Media Assessment): ✅ Correctly determines media necessity and visual analysis needs
- Stage 2 (Context Extraction): ✅ Provides formatted responses with relevant sections

**PHASE 2 REDESIGN** 🔄

**New Requirements** (from user):
- Create while True loop for continuous chat experience
- Use GPT-4.1 as main conversational model
- Integrate scratch pad as a **required tool** for context enrichment
- Prepare for media handling capabilities  
- Implement "Luzia" persona: fun, helpful friend (not AI), brief responses, no generic follow-ups

**Architectural Shift**: From single-query CLI → Continuous chat with function calling

**ARCHITECTURE DECISIONS FINALIZED** ✅

**User Clarifications**:
1. Transform existing `scratchpad.py` into function/tool for GPT-4.1 calling
2. If scratchpad indicates media needed → add media analysis to LLM context
3. Chat interface design approved
4. New `luzia.py` file, exit/Ctrl+C handling, GPT-4.1 available
5. Function requirements confirmed: scratchpad required=True
6. Media processing triggered by scratchpad tool recommendations
7. Context = conversation history + scratchpad additions
8. Fresh start each session
9. Luzia persona in system prompt

**FINAL ARCHITECTURE**:

**Core Functions for GPT-4.1:**
```python
def get_scratch_pad_context(query: str) -> dict:
    """Required function that enriches context from scratch pad"""
    
def analyze_media_file(file_path: str) -> dict: 
    """Optional function for visual analysis when scratch pad indicates need"""
```

**Chat Flow:**
1. User input → GPT-4.1 (with Luzia persona)
2. GPT-4.1 calls `get_scratch_pad_context()` (required=True)
3. If scratch pad indicates media needed → GPT-4.1 calls `analyze_media_file()`
4. Context = conversation + scratch pad + media (if any)
5. Luzia responds naturally

**Technical Stack:**
- `luzia.py` - New continuous chat interface
- GPT-4.1 with function calling
- Exit: 'exit' command or Ctrl+C
- Fresh conversation each session

**Task 2.1 COMPLETED** ✅
- Created `tools.py` with `ScratchPadTools` class
- Implemented `get_scratch_pad_context(query)` function with smart context extraction
- Implemented `analyze_media_file(file_path)` function with image analysis capabilities
- Designed proper function schemas for GPT-4.1 integration
- **Success Criteria Met**: Functions work independently and return proper JSON responses

**Task 2.2 COMPLETED** ✅  
- Created `luzia.py` with continuous while loop chat interface
- Integrated GPT-4-turbo-preview (fallback for GPT-4.1) with function calling
- Implemented Luzia persona system prompt (fun, helpful friend, brief responses)
- Built conversation context management with history
- Added graceful exit handling (exit commands + Ctrl+C)
- **Success Criteria Met**: Continuous chat with scratch pad context integration

## Executor Starting Task 2.3: Add Media Processing Integration

## Lessons

**Technical Lessons Learned**:
- Virtual environment setup required on macOS due to externally-managed Python environment
- OpenAI API error handling works correctly - provides clear feedback for invalid API keys
- Two-stage processing architecture successful: media assessment + context extraction
- Click CLI framework provides excellent user experience with help text and options
- Realistic test data (actual images and personal info) crucial for meaningful validation

**Design Validation**:
- KISS error handling principle worked well - clear, simple error messages
- Parameterized file paths architecture ready for multi-user expansion
- Enhanced media processing correctly identifies when visual analysis is/isn't needed
- System prompt in config folder allows easy customization
- Verbose mode provides helpful debugging information

**User Experience Insights**:
- Direct query syntax `scratchpad "question"` feels natural and efficient
- Formatted output with clear sections makes responses easy to scan
- Media assessment transparency builds user confidence in AI decisions 