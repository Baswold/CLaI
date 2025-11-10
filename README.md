# CLaI - Command Line AI Assistant

CLaI is a powerful command-line coding assistant that can execute shell commands to help you with development tasks. It supports multiple AI providers including OpenAI and OpenRouter, with enhanced UI and improved tool calling for smaller models.

## Features

- **Beautiful Terminal UI**: Rich terminal interface with colors, panels, and syntax highlighting
- **Multiple AI Providers**: Support for both OpenAI and OpenRouter APIs
- **Dynamic Model List**: Constantly updating list of available models from OpenRouter
- **Enhanced Tool Calling**: Optimized prompts and examples for better performance with smaller models
- **Shell Command Execution**: Can run any shell command to inspect files, run code, and more
- **Conversation History**: Maintains context across interactions
- **Interactive Commands**: Special commands for model listing and history management

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Baswold/CLaI.git
cd CLaI
```

2. Install dependencies:
```bash
pip install rich requests openai
```

3. Set up your API key(s):

For OpenAI:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

For OpenRouter:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

Run with OpenAI (default):
```bash
python clai.py
```

Run with a specific OpenAI model:
```bash
python clai.py --model gpt-4o-mini
```

Run with OpenRouter:
```bash
python clai.py --provider openrouter --model openai/gpt-4o
```

### List Available Models

See all available OpenRouter models:
```bash
python clai.py --list-models
```

Or use the `/models` command during a session:
```
You> /models
```

### Interactive Commands

While running CLaI, you can use these special commands:

- `/models` - List all available OpenRouter models with pricing
- `/clear` - Clear conversation history
- `exit` or `quit` - Exit the program

### Examples

**Using OpenAI:**
```bash
export OPENAI_API_KEY="sk-..."
python clai.py --model gpt-4o-mini

You> What files are in the current directory?
# The assistant will use the run_shell tool to execute 'ls -la'
```

**Using OpenRouter with a small model:**
```bash
export OPENROUTER_API_KEY="sk-..."
python clai.py --provider openrouter --model google/gemini-flash-1.5

You> Create a simple Python script that prints hello world
# The assistant will create the file and can even run it for you
```

**Browsing available models:**
```bash
python clai.py --list-models
# Shows a table of all available OpenRouter models with their context lengths and pricing
```

## How It Works

CLaI uses an agentic architecture where the AI model can:

1. **Understand your request**: Parse natural language questions and commands
2. **Plan actions**: Decide what shell commands to run
3. **Execute tools**: Run shell commands using the `run_shell` tool
4. **Analyze results**: Read command output and provide helpful explanations
5. **Iterate**: Continue calling tools until the task is complete

### Enhanced Tool Calling for Small Models

The system prompt includes:
- Clear guidelines on when and how to use tools
- Step-by-step thinking instructions
- Multiple examples of tool usage patterns
- Explicit formatting requirements

This helps smaller, less capable models understand how to properly use the tool calling interface.

### OpenRouter Integration

OpenRouter support includes:
- Dynamic model fetching (updated every hour)
- Model list caching for performance
- Support for all OpenRouter models that support function calling
- Pricing information display
- Automatic model discovery

### UI Enhancements

When the `rich` library is available:
- Colorful, formatted output with panels and borders
- Syntax highlighting for command output
- Beautiful tables for model listings
- Markdown rendering for assistant responses
- Better error messages with color coding

Falls back to plain text output if `rich` is not installed.

## Security Note

CLaI can execute arbitrary shell commands on your system. Only use it in environments where you trust the AI model's decisions, and always review commands before they execute (they are displayed in the terminal).

Shell commands run by the assistant are always echoed to the terminal so you can see exactly what was executed.

## Requirements

- Python 3.7+
- `openai` - OpenAI API client
- `rich` - Terminal formatting (optional but recommended)
- `requests` - HTTP library for OpenRouter (optional, needed for OpenRouter only)

## Troubleshooting

**"OPENAI_API_KEY environment variable is not set"**
- Make sure you've exported your API key: `export OPENAI_API_KEY="..."`

**"OPENROUTER_API_KEY environment variable is not set"**
- If using OpenRouter, export your key: `export OPENROUTER_API_KEY="..."`

**"Warning: 'rich' library not available"**
- Install rich for better UI: `pip install rich`
- The program will still work without it, just with plain text output

**"Warning: Could not fetch OpenRouter models"**
- Check your internet connection
- Verify your OpenRouter API key is correct
- The program will use cached models if available

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

MIT License - feel free to use this however you like!
