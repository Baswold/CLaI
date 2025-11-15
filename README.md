# CLaI - Command-Line AI Assistant

CLaI is a powerful command-line coding assistant with a beautiful terminal UI, comprehensive file operations, and support for multiple LLM providers. Designed to work seamlessly with both large frontier models and small high-reasoning models.

## ✨ Features

### 🎨 Beautiful Terminal UI
- **Rich formatting** with colors, panels, and markdown rendering
- **Syntax highlighting** for code blocks
- **Progress indicators** for long-running operations
- **Clear visual feedback** for tool usage

### 🛠️ Comprehensive Tool Suite
- **`read_file`** - Read file contents with optional line ranges
- **`write_file`** - Create or overwrite files
- **`edit_file`** - Make surgical edits by replacing text
- **`list_files`** - List directory contents with glob pattern support
- **`search_files`** - Search for patterns in files (regex support)
- **`run_shell`** - Execute shell commands (git, build tools, etc.)
- **`get_cwd`** - Get current working directory

### 🤖 Multi-Provider LLM Support
- **OpenAI** (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
- **Anthropic Claude** (Claude 3.5 Sonnet, Claude 3.5 Haiku)
- **Optimized for small high-reasoning models** with clear, structured prompts

### ⚙️ Configuration
- YAML-based configuration file support (`~/.clai/config.yaml`)
- Environment variable support for API keys
- Command-line arguments for quick overrides

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CLaI.git
cd CLaI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API key:
```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Basic Usage

Run with OpenAI (default):
```bash
python clai.py
```

Run with Anthropic Claude:
```bash
python clai.py --provider anthropic
```

Specify a different model:
```bash
python clai.py --model gpt-4o-mini
python clai.py --provider anthropic --model claude-3-5-haiku-20241022
```

### Commands

- Type your request at the `user>` prompt
- Type `exit` or `quit` to end the session
- Press `Ctrl+D` to exit
- Press `Ctrl+C` to cancel current input

## 📝 Configuration File

Create `~/.clai/config.yaml` to set defaults:

```yaml
# Default LLM provider
provider: openai

# OpenAI Configuration
openai_api_key: sk-...  # Optional if using env var
openai_model: gpt-4o-mini

# Anthropic Configuration
anthropic_api_key: sk-ant-...  # Optional if using env var
anthropic_model: claude-3-5-haiku-20241022
```

See `config.example.yaml` for a complete example.

## 🧠 Recommended Models

### For Budget-Conscious Usage (Small High-Reasoning Models)
- **Claude 3.5 Haiku** (`claude-3-5-haiku-20241022`) - Fast, cheap, excellent reasoning
- **GPT-4o Mini** (`gpt-4o-mini`) - Fast, affordable, good reasoning

### For Best Performance
- **Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`) - Excellent reasoning and coding
- **GPT-4o** (`gpt-4o`) - Strong all-around performance

## 💡 Example Usage

```
user> Can you help me refactor the authentication module?

🔧 search_files({"pattern": "auth", "file_pattern": "*.py"})
🔧 read_file({"file_path": "src/auth.py"})

assistant> I found the authentication module. Here's my analysis...

[The assistant provides detailed analysis with markdown formatting]
```

## 🔧 Tool Descriptions

| Tool | Description | Example |
|------|-------------|---------|
| `read_file` | Read file contents | `read_file("config.py", start_line=10, end_line=20)` |
| `write_file` | Create/overwrite files | `write_file("output.txt", "Hello World")` |
| `edit_file` | Replace text in files | `edit_file("app.py", "old_name", "new_name")` |
| `list_files` | List directory contents | `list_files(".", "*.py")` |
| `search_files` | Search in files | `search_files("TODO", ".", "*.py")` |
| `run_shell` | Execute commands | `run_shell("git status")` |
| `get_cwd` | Get working directory | `get_cwd()` |

## 🎯 Design Philosophy

CLaI is designed to be:

1. **Simple** - Single-file architecture, minimal dependencies
2. **Powerful** - Comprehensive file and shell operations
3. **Beautiful** - Rich terminal UI inspired by Claude Code
4. **Efficient** - Optimized for small high-reasoning models
5. **Flexible** - Multiple provider support with easy configuration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## 📄 License

MIT License - feel free to use this in your own projects!

## 🙏 Acknowledgments

- Inspired by [Claude Code](https://docs.claude.com/en/docs/claude-code)
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Powered by OpenAI and Anthropic APIs
