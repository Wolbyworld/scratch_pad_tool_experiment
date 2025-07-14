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
**Task 2.1**: Implement File Loading and Parsing
- Create module to discover and load scratch pad files
- Parse sections and extract structured data
- **Success Criteria**: Can successfully load and parse template file

**Task 2.2**: Integrate OpenAI API
- Set up OpenAI client with GPT-4o-mini
- Design prompt for context extraction
- Handle API responses and errors
- **Success Criteria**: Can make successful API calls with sample data

**Task 2.3**: Build Query Processing Engine
- Combine file parsing with AI processing
- Extract relevant context based on user query
- Format and return results
- **Success Criteria**: Can process simple queries and return relevant context

### Phase 3: User Interface
**Task 3.1**: Create Command Line Interface
- Build CLI with argument parsing
- Handle user input and display results
- Add help documentation
- **Success Criteria**: Functional CLI that processes queries end-to-end

### Phase 4: Polish and Testing
**Task 4.1**: Add Configuration Management
- Handle API key configuration
- Add settings for file paths and behavior
- **Success Criteria**: Tool works without hardcoded values

**Task 4.2**: Implement Error Handling
- Handle missing files, API errors, malformed queries
- Provide helpful error messages
- **Success Criteria**: Tool gracefully handles common error scenarios

**Task 4.3**: Create Documentation and Examples
- Write README with setup and usage instructions
- Create example scratch pad files
- **Success Criteria**: New user can set up and use tool following documentation

## Project Status Board

### Phase 1: Foundation and Design
- [ ] Task 1.1: Create Scratch Pad Template
- [ ] Task 1.2: Define Technical Architecture

### Phase 2: Core Functionality  
- [ ] Task 2.1: Implement File Loading and Parsing
- [ ] Task 2.2: Integrate OpenAI API
- [ ] Task 2.3: Build Query Processing Engine

### Phase 3: User Interface
- [ ] Task 3.1: Create Command Line Interface

### Phase 4: Polish and Testing
- [ ] Task 4.1: Add Configuration Management
- [ ] Task 4.2: Implement Error Handling
- [ ] Task 4.3: Create Documentation and Examples

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

**Next Milestone**: Ready to switch to Executor mode for implementation

## Executor's Feedback or Assistance Requests

*To be filled by Executor*

## Lessons

*To be documented throughout the project* 