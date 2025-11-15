#!/usr/bin/env python3
"""
CLaI - Command-Line AI Assistant
A powerful coding assistant with rich UI and comprehensive tools.
"""

import os
import sys
import json
import argparse
import subprocess
import readline
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.theme import Theme
except ImportError:
    print("Error: 'rich' library not found. Install with: pip install rich")
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None

# Initialize Rich console with custom theme
custom_theme = Theme({
    "user": "bold cyan",
    "assistant": "bold green",
    "tool": "bold yellow",
    "error": "bold red",
    "system": "dim",
})
console = Console(theme=custom_theme)


# ============================================================================
# Tool Implementations
# ============================================================================

def read_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """Read contents of a file, optionally specifying line range."""
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"Error: File '{file_path}' does not exist"
        if not path.is_file():
            return f"Error: '{file_path}' is not a file"

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if start_line is not None or end_line is not None:
            start = (start_line or 1) - 1
            end = end_line if end_line is not None else len(lines)
            lines = lines[start:end]

        content = ''.join(lines)
        return content if content else "(empty file)"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file (creates or overwrites)."""
    try:
        path = Path(file_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def edit_file(file_path: str, old_text: str, new_text: str) -> str:
    """Edit a file by replacing old_text with new_text."""
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"Error: File '{file_path}' does not exist"

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_text not in content:
            return f"Error: Text to replace not found in file"

        new_content = content.replace(old_text, new_text, 1)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return f"Successfully edited '{file_path}'"
    except Exception as e:
        return f"Error editing file: {str(e)}"


def list_files(directory: str = ".", pattern: str = "*") -> str:
    """List files in a directory matching a pattern (supports glob patterns)."""
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist"
        if not path.is_dir():
            return f"Error: '{directory}' is not a directory"

        # Use rglob for ** patterns, glob otherwise
        if "**" in pattern:
            files = sorted(path.rglob(pattern.replace("**/", "")))
        else:
            files = sorted(path.glob(pattern))

        if not files:
            return f"No files matching '{pattern}' found in '{directory}'"

        result = []
        for f in files[:100]:  # Limit to 100 files
            rel_path = f.relative_to(path) if f.is_relative_to(path) else f
            if f.is_dir():
                result.append(f"{rel_path}/")
            else:
                size = f.stat().st_size
                result.append(f"{rel_path} ({size} bytes)")

        if len(files) > 100:
            result.append(f"... and {len(files) - 100} more files")

        return "\n".join(result)
    except Exception as e:
        return f"Error listing files: {str(e)}"


def search_files(pattern: str, directory: str = ".", file_pattern: str = "*") -> str:
    """Search for a pattern in files (like grep)."""
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist"

        matches = []
        files_searched = 0

        for file_path in path.rglob(file_pattern):
            if not file_path.is_file():
                continue

            # Skip binary files and common ignore patterns
            if file_path.suffix in ['.pyc', '.so', '.dylib', '.dll', '.exe']:
                continue
            if any(part.startswith('.') for part in file_path.parts):
                continue

            files_searched += 1
            if files_searched > 1000:  # Limit files searched
                break

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            rel_path = file_path.relative_to(path)
                            matches.append(f"{rel_path}:{line_num}: {line.rstrip()}")
                            if len(matches) >= 100:  # Limit results
                                break
            except (UnicodeDecodeError, PermissionError):
                continue

            if len(matches) >= 100:
                break

        if not matches:
            return f"No matches found for pattern '{pattern}'"

        result = "\n".join(matches)
        if files_searched >= 1000 or len(matches) >= 100:
            result += f"\n\n(search limited to {files_searched} files, {len(matches)} matches shown)"

        return result
    except Exception as e:
        return f"Error searching files: {str(e)}"


def run_shell(command: str) -> str:
    """Execute a shell command and return its output."""
    console.print(f"[tool]$ {command}[/tool]")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
        )
        output = result.stdout if result.stdout else "(no output)"
        console.print(output, style="system")
        return output
    except subprocess.TimeoutExpired:
        err = "Error: Command timed out after 30 seconds"
        console.print(err, style="error")
        return err
    except Exception as e:
        err = f"Error running command: {str(e)}"
        console.print(err, style="error")
        return err


def get_cwd() -> str:
    """Get the current working directory."""
    return str(Path.cwd())


# ============================================================================
# Tool Definitions for LLM
# ============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Returns the file content as text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional starting line number (1-indexed)",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional ending line number",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates new file or overwrites existing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by replacing specific text. Use for surgical edits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to edit",
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Exact text to find and replace",
                    },
                    "new_text": {
                        "type": "string",
                        "description": "New text to replace with",
                    },
                },
                "required": ["file_path", "old_text", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory. Supports glob patterns like *.py or **/*.js",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to list (default: current directory)",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match files (default: *)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for a pattern in files (like grep). Supports regex patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in (default: current directory)",
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Glob pattern for files to search (default: *)",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell command and return the output. Use for git, build tools, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cwd",
            "description": "Get the current working directory path.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# Map tool names to implementations
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "list_files": list_files,
    "search_files": search_files,
    "run_shell": run_shell,
    "get_cwd": get_cwd,
}


# ============================================================================
# System Prompts optimized for small reasoning models
# ============================================================================

SYSTEM_PROMPT = """You are CLaI, a command-line coding assistant with comprehensive file and shell access.

AVAILABLE TOOLS:
- read_file: Read file contents (with optional line range)
- write_file: Create or overwrite files
- edit_file: Make surgical edits by replacing text
- list_files: List directory contents (supports glob patterns)
- search_files: Search for patterns in files (regex support)
- run_shell: Execute shell commands (git, build tools, etc.)
- get_cwd: Get current working directory

WORKFLOW:
1. Think step-by-step before using tools
2. Use read_file to understand code before editing
3. Use search_files to find relevant files
4. Make targeted edits with edit_file for small changes
5. Use write_file for new files or complete rewrites
6. Explain what you're doing clearly and concisely

BEST PRACTICES:
- Always verify file contents before editing
- Use search to understand codebase structure
- Execute one logical step at a time
- Provide clear explanations of your actions
- Handle errors gracefully and explain issues

Be helpful, precise, and efficient. Focus on solving the user's problem effectively."""


# ============================================================================
# LLM Provider Support
# ============================================================================

class LLMProvider:
    """Base class for LLM providers."""

    def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Send a chat request and return the response."""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        try:
            import openai
            self.client = openai
            self.client.api_key = api_key
        except ImportError:
            console.print("[error]Error: openai library not installed. Install with: pip install openai[/error]")
            sys.exit(1)

    def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        response = self.client.ChatCompletion.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )
        return response.choices[0].message


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            console.print("[error]Error: anthropic library not installed. Install with: pip install anthropic[/error]")
            sys.exit(1)

    def chat(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        # Convert OpenAI-style messages to Anthropic format
        system_msg = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                anthropic_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                if isinstance(msg.get("content"), str):
                    anthropic_messages.append({"role": "assistant", "content": msg["content"]})
                elif msg.get("tool_calls"):
                    # Convert tool calls to Anthropic format
                    content = []
                    for tc in msg["tool_calls"]:
                        content.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                        })
                    anthropic_messages.append({"role": "assistant", "content": content})
            elif msg["role"] == "tool":
                # Tool results
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": msg["content"]
                    }]
                })

        # Convert tools to Anthropic format
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"]
            })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_msg or SYSTEM_PROMPT,
            messages=anthropic_messages,
            tools=anthropic_tools
        )

        # Convert response back to OpenAI format
        result = {"content": None, "tool_calls": None}

        for block in response.content:
            if block.type == "text":
                result["content"] = block.text
            elif block.type == "tool_use":
                if not result["tool_calls"]:
                    result["tool_calls"] = []
                result["tool_calls"].append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input)
                    }
                })

        return type('Message', (), result)()


# ============================================================================
# Configuration Loading
# ============================================================================

def load_config() -> Dict:
    """Load configuration from config.yaml if it exists."""
    config_path = Path.home() / ".clai" / "config.yaml"
    if not config_path.exists() or not yaml:
        return {}

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        console.print(f"[error]Warning: Could not load config: {e}[/error]")
        return {}


# ============================================================================
# Main Application
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CLaI - Command-Line AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use (default: openai)",
    )
    parser.add_argument(
        "--model",
        help="Model to use (provider-specific)",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Show configuration and exit",
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config()

    if args.config:
        console.print(Panel(
            json.dumps(config, indent=2),
            title="Configuration",
            border_style="cyan"
        ))
        return

    # Initialize LLM provider
    provider_name = args.provider or config.get("provider", "openai")

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY") or config.get("openai_api_key")
        if not api_key:
            console.print("[error]Error: OPENAI_API_KEY environment variable not set[/error]")
            return
        model = args.model or config.get("openai_model", "gpt-4o")
        provider = OpenAIProvider(api_key, model)

    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY") or config.get("anthropic_api_key")
        if not api_key:
            console.print("[error]Error: ANTHROPIC_API_KEY environment variable not set[/error]")
            return
        model = args.model or config.get("anthropic_model", "claude-3-5-sonnet-20241022")
        provider = AnthropicProvider(api_key, model)

    # Display welcome message
    console.print(Panel(
        f"[bold]CLaI - Command-Line AI Assistant[/bold]\n\n"
        f"Provider: {provider_name}\n"
        f"Model: {provider.model}\n"
        f"Working Directory: {Path.cwd()}\n\n"
        f"Type 'exit' or 'quit' to end session, Ctrl+D to exit",
        border_style="cyan"
    ))

    # Initialize conversation
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Main REPL loop
    while True:
        try:
            user_input = console.input("[user]user>[/user] ")
        except EOFError:
            console.print("\n[system]Goodbye![/system]")
            break
        except KeyboardInterrupt:
            console.print("\n[system]Use 'exit' or Ctrl+D to quit[/system]")
            continue

        if not user_input.strip():
            continue

        if user_input.lower().strip() in {"exit", "quit"}:
            console.print("[system]Goodbye![/system]")
            break

        messages.append({"role": "user", "content": user_input})

        # Agent loop - handle tool calls
        with console.status("[bold green]Thinking...", spinner="dots"):
            while True:
                try:
                    response = provider.chat(messages, TOOLS)
                except Exception as e:
                    console.print(f"[error]Error: {str(e)}[/error]")
                    messages.pop()  # Remove user message
                    break

                # Add assistant message
                if hasattr(response, '__dict__'):
                    # Convert to dict for storage
                    msg_dict = {"role": "assistant"}
                    if response.content:
                        msg_dict["content"] = response.content
                    if response.tool_calls:
                        msg_dict["tool_calls"] = [
                            {
                                "id": tc.id if hasattr(tc, 'id') else tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc.function.name if hasattr(tc.function, 'name') else tc["function"]["name"],
                                    "arguments": tc.function.arguments if hasattr(tc.function, 'arguments') else tc["function"]["arguments"]
                                }
                            }
                            for tc in response.tool_calls
                        ]
                    messages.append(msg_dict)
                else:
                    messages.append(response)

                # Handle tool calls
                if response.tool_calls:
                    for call in response.tool_calls:
                        func_name = call.function.name if hasattr(call.function, 'name') else call["function"]["name"]
                        func_args_str = call.function.arguments if hasattr(call.function, 'arguments') else call["function"]["arguments"]

                        console.print(f"[tool]🔧 {func_name}({func_args_str})[/tool]")

                        try:
                            func_args = json.loads(func_args_str)
                            func = TOOL_FUNCTIONS.get(func_name)

                            if func:
                                output = func(**func_args)
                            else:
                                output = f"Error: Unknown tool '{func_name}'"

                            call_id = call.id if hasattr(call, 'id') else call["id"]
                            messages.append({
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": output,
                            })
                        except Exception as e:
                            console.print(f"[error]Tool error: {str(e)}[/error]")
                            call_id = call.id if hasattr(call, 'id') else call["id"]
                            messages.append({
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": f"Error: {str(e)}",
                            })
                    continue

                # Display assistant response
                if response.content:
                    console.print(f"\n[assistant]assistant>[/assistant]", end=" ")

                    # Try to render as markdown if it contains code blocks or formatting
                    content = response.content
                    if "```" in content or "#" in content or "*" in content:
                        try:
                            console.print(Markdown(content))
                        except:
                            console.print(content)
                    else:
                        console.print(content)
                    console.print()

                break


if __name__ == "__main__":
    main()
