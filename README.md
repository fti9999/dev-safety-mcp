# Development Safety System - MCP Server

An MCP (Model Control Protocol) server that enables session continuity and sandbox safety for LLM development workflows.

## 🎯 Core Goal

Create an MCP server that provides "pick up exactly where you left off" + "never break the main app" functionality for AI-assisted development.

## ✨ Key Features

- **Session State Persistence**: Save and restore complete development session context
- **Sandbox Management**: Isolated development environments for safe experimentation  
- **Activity Detection**: File-based monitoring to suggest when to save session state
- **Safe Synchronization**: Controlled copying of approved changes back to main project

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd dev-safety-mcp

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Basic Usage

1. **Create a sandbox for safe development:**
```python
# Through MCP client
await create_sandbox("F:/my-project")
```

2. **Save your session state when taking a break:**
```python
await save_session_state(
    operation="Add payment feature",
    current_step="Created component files", 
    next_steps=["Add API endpoints", "Test integration"],
    sandbox_path="F:/my-project-sandbox-session-20250604-143022",
    context={"feature": "payment", "priority": "high"}
)
```

3. **Continue where you left off:**
```python
session = await load_session_state()
print(session['continuation_prompt'])
```

4. **Sync approved changes to main project:**
```python
await sync_to_main(
    sandbox_path="F:/my-project-sandbox-session-20250604-143022",
    main_path="F:/my-project",
    files=["src/components/Payment.jsx", "src/api/payment.js"]
)
```

## 🛠️ Available MCP Tools

### `create_sandbox`
Creates an isolated copy of your project for safe development.

**Parameters:**
- `project_path` (str): Path to the main project
- `sandbox_name` (str, optional): Custom name for the sandbox

### `save_session_state`
Saves complete session context for later continuation.

**Parameters:**
- `operation` (str): Description of what you're working on
- `current_step` (str): What was just completed
- `next_steps` (List[str]): What needs to be done next
- `sandbox_path` (str): Path to the sandbox being used
- `context` (Dict): Additional context information

### `load_session_state`
Loads the most recent session state and provides continuation prompt.

### `check_activity`
Monitors file activity in the sandbox to suggest when to save state.

**Parameters:**
- `sandbox_path` (str): Path to monitor
- `minutes` (int, optional): Time window to check (default: 10)

### `sync_to_main`
Safely copies approved changes from sandbox to main project.

**Parameters:**
- `sandbox_path` (str): Source sandbox path
- `main_path` (str): Destination main project path  
- `files` (List[str], optional): Specific files to sync (default: all changed files)

## 📁 Project Structure

```bash

dev-safety-mcp/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   └── project_types.json
├── src/
│   ├── __init__.py
│   ├── mcp_server.py              # Main MCP server
│   ├── sandbox_manager.py         # Sandbox creation/management
│   ├── session_manager.py         # Session state persistence
│   ├── activity_monitor.py        # File-based activity detection
│   └── utils.py                   # Helper functions
├── tests/
│   ├── test_basic_functionality.py
│   └── test_with_real_project.py
└── examples/
    └── basic_workflow_example.py

```

## 🔧 Development Workflow

1. **Start development** - Create sandbox with `create_sandbox`
2. **Work safely** - All changes happen in isolated sandbox
3. **Save progress** - Use `save_session_state` when taking breaks
4. **Continue seamlessly** - Load session state to pick up exactly where you left off
5. **Deploy changes** - Use `sync_to_main` to copy approved changes back

## 🛡️ Safety Features

- **Sandbox Isolation**: Main project never touched during development
- **Automatic Backups**: Backups created before any sync operations
- **Activity Monitoring**: Suggests saving state during periods of inactivity
- **Version Control**: Git branching used in sandboxes for change tracking

## 🧪 Testing

```bash
# Run basic functionality tests
python -m pytest tests/test_basic_functionality.py

# Test with a real project
python -m pytest tests/test_with_real_project.py

# Run example workflow
python examples/basic_workflow_example.py
```

## 📋 Requirements

- Python 3.8+
- Git (for sandbox version control)
- MCP compatible client (Claude Desktop, etc.)

## 🚧 Implementation Status

### ✅ Phase 1: Core Value (Current)
- [x] MCP Server with session continuity tools
- [x] Sandbox Management for safe development  
- [x] Session State Persistence
- [x] File-Based Activity Detection
- [x] Manual Session Continuation

### 🔮 Future Phases
- **Phase 2**: Smart Hints (timer-based monitoring, auto-suggestions)
- **Phase 3**: Simple Automation (auto-save, health checking)
- **Phase 4**: Advanced Features (multi-interface support, visual monitoring)

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For issues and questions, please use the GitHub issue tracker.