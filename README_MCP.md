# MCP Memory Integration for Luzia

## Overview

Luzia now supports two memory systems:
- **Scratchpad** (default): File-based memory using `scratchpad.txt`
- **MCP**: Knowledge graph memory using Model Context Protocol

## Features

### Memory System Selection

Choose your memory system at startup:

```bash
# Interactive selection
python luzia.py

# Direct selection
python luzia.py --memory=scratchpad
python luzia.py --memory=mcp

# Help
python luzia.py --help
```

### Memory Systems Comparison

| Feature | Scratchpad | MCP |
|---------|------------|-----|
| **Storage** | Text file | Knowledge graph |
| **Structure** | Sections & plain text | Entities, relations, observations |
| **Queries** | Text search | Graph traversal |
| **Persistence** | File-based | JSON database |
| **Setup** | Ready to use | Requires MCP server |

### MCP Knowledge Graph

The MCP system stores information as:
- **Entities**: People, projects, topics (nodes)
- **Relations**: Connections between entities (edges)  
- **Observations**: Facts about entities (attributes)

Example:
```
[User] --works_on--> [Python Project]
[User] --prefers--> [Morning meetings]
[Python Project] --uses--> [FastAPI]
```

## Configuration

### Environment Variables

```bash
# .env file
MEMORY_SYSTEM=scratchpad  # or "mcp"
OPENAI_API_KEY=your_key_here
```

### MCP Server Setup

The MCP memory server is automatically installed and configured:

```json
// config/mcp_config.json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "./data/mcp_memory.json"
      }
    }
  }
}
```

## Usage Examples

### Scratchpad System
```
🧠 Using Scratchpad memory system
🔍 Checking scratchpad memory for: What projects am I working on?
✅ scratchpad context: Current Projects: Luzia AI Assistant, MCP Integration...
```

### MCP System  
```
🧠 Using MCP Knowledge Graph memory system
🔍 Checking MCP memory for: What projects am I working on?
✅ MCP context: Retrieved from MCP knowledge graph...
```

## Architecture

```
Memory Manager
├── Scratchpad Memory (ScratchpadMemory)
│   └── File-based storage via ScratchPadTools
└── MCP Memory (MCPMemory)
    └── Graph-based storage via OpenAI Responses API + MCP Server
```

## Benefits

### Scratchpad Memory
- ✅ Simple setup
- ✅ Human-readable
- ✅ Fast retrieval
- ✅ Existing data preserved

### MCP Memory  
- ✅ Structured relationships
- ✅ Rich querying capabilities
- ✅ Scalable storage
- ✅ Graph-based insights

## Migration

Currently, both systems run independently. The MCP system starts with an empty knowledge graph and learns from conversations.

Future versions will include migration tools to convert scratchpad data to MCP format.

## Technical Details

- **Interface**: `MemoryInterface` abstract base class
- **Manager**: `MemoryManager` handles system selection
- **Fallback**: MCP gracefully falls back to scratchpad on errors
- **API**: Uses OpenAI Responses API for MCP communication

## Status

- ✅ Memory system selection
- ✅ Scratchpad adapter
- ✅ MCP integration
- ✅ Context retrieval
- ✅ Information storage
- ⏳ Data migration tools (planned)
- ⏳ Graph visualization (planned) 