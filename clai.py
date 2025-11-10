import os
import subprocess
import json
import argparse
import readline
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.prompt import Prompt
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: 'rich' library not available. Install with: pip install rich")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' library not available. Install with: pip install requests")

# Initialize console for rich output
console = Console() if RICH_AVAILABLE else None

# Cache for OpenRouter models
MODELS_CACHE = {
    "models": [],
    "last_updated": None,
    "ttl": timedelta(hours=1)  # Refresh every hour
}

def run_shell(command: str) -> str:
    """Execute a shell command and return its output."""
    if RICH_AVAILABLE:
        console.print(f"[bold cyan]$ {command}[/bold cyan]")
    else:
        print(f"$ {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if RICH_AVAILABLE:
            syntax = Syntax(result.stdout, "bash", theme="monokai", line_numbers=False)
            console.print(syntax)
        else:
            print(result.stdout)

        return result.stdout
    except Exception as e:
        err = f"Error running command: {e}"
        if RICH_AVAILABLE:
            console.print(f"[bold red]{err}[/bold red]")
        else:
            print(err)
        return err

def fetch_openrouter_models() -> List[Dict[str, Any]]:
    """Fetch available models from OpenRouter API with caching."""
    if not REQUESTS_AVAILABLE:
        return []

    # Check cache first
    now = datetime.now()
    if (MODELS_CACHE["models"] and
        MODELS_CACHE["last_updated"] and
        now - MODELS_CACHE["last_updated"] < MODELS_CACHE["ttl"]):
        return MODELS_CACHE["models"]

    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            MODELS_CACHE["models"] = models
            MODELS_CACHE["last_updated"] = now
            return models
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[yellow]Warning: Could not fetch OpenRouter models: {e}[/yellow]")
        else:
            print(f"Warning: Could not fetch OpenRouter models: {e}")

    return MODELS_CACHE["models"]

def list_openrouter_models():
    """Display available OpenRouter models in a nice table."""
    models = fetch_openrouter_models()

    if not models:
        if RICH_AVAILABLE:
            console.print("[yellow]No models available or could not fetch from OpenRouter[/yellow]")
        else:
            print("No models available or could not fetch from OpenRouter")
        return

    if RICH_AVAILABLE:
        table = Table(title="OpenRouter Models")
        table.add_column("Model ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Context", justify="right", style="yellow")
        table.add_column("Pricing (per 1M tokens)", style="magenta")

        for model in models[:50]:  # Show first 50
            model_id = model.get("id", "N/A")
            name = model.get("name", "N/A")
            context = str(model.get("context_length", "N/A"))

            pricing = model.get("pricing", {})
            prompt_price = float(pricing.get("prompt", 0)) * 1000000
            completion_price = float(pricing.get("completion", 0)) * 1000000
            price_str = f"${prompt_price:.2f}/${completion_price:.2f}"

            table.add_row(model_id, name, context, price_str)

        console.print(table)
        console.print(f"\n[dim]Showing {min(50, len(models))} of {len(models)} models[/dim]")
    else:
        print("\nAvailable OpenRouter Models:")
        for i, model in enumerate(models[:50], 1):
            print(f"{i}. {model.get('id', 'N/A')} - {model.get('name', 'N/A')}")
        print(f"\nShowing {min(50, len(models))} of {len(models)} models")

# Enhanced system prompt for better tool calling with small models
SYSTEM_PROMPT = """You are CLaI, a command-line coding assistant running in a local shell.

You have access to the `run_shell` tool which lets you execute shell commands.

IMPORTANT GUIDELINES FOR TOOL USE:
1. Always use the run_shell tool when you need to:
   - Check files or directories (ls, cat, find, etc.)
   - Run code or scripts
   - Install packages
   - Check system information
   - Perform any file operations

2. When using tools, think step by step:
   - First, explain what you're going to do
   - Then use the tool
   - Finally, explain the results

3. Format your tool calls correctly:
   - Tool name: "run_shell"
   - Parameter: "command" (must be a valid shell command)

EXAMPLES:

User: "What files are in this directory?"
You should think: I need to list files, so I'll use the run_shell tool with 'ls -la'
Tool call: {"name": "run_shell", "arguments": {"command": "ls -la"}}

User: "Create a file called test.txt with 'hello' in it"
You should think: I'll use echo to create the file
Tool call: {"name": "run_shell", "arguments": {"command": "echo 'hello' > test.txt"}}

User: "What Python version is installed?"
You should think: I'll check the Python version
Tool call: {"name": "run_shell", "arguments": {"command": "python --version"}}

Remember: ALWAYS use the tool for any operation that requires accessing the system!
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell command and return the output. Use this for ANY filesystem operation, running code, checking system info, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute (e.g., 'ls -la', 'python script.py', 'cat file.txt')",
                    }
                },
                "required": ["command"],
            },
        },
    }
]

def call_openai_api(model: str, messages: List[Dict], tools: List[Dict]) -> Dict:
    """Call OpenAI API."""
    import openai

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        tools=tools,
    )
    return response.choices[0].message

def call_openrouter_api(model: str, messages: List[Dict], tools: List[Dict], api_key: str) -> Dict:
    """Call OpenRouter API."""
    if not REQUESTS_AVAILABLE:
        raise Exception("requests library is required for OpenRouter. Install with: pip install requests")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/yourusername/CLaI",
        "X-Title": "CLaI",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": messages,
        "tools": tools,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

    result = response.json()
    return result["choices"][0]["message"]

def print_assistant_message(content: str):
    """Print assistant message with nice formatting."""
    if RICH_AVAILABLE:
        console.print(Panel(
            Markdown(content),
            title="[bold green]Assistant[/bold green]",
            border_style="green"
        ))
    else:
        print(f"\nassistant> {content}\n")

def print_welcome():
    """Print welcome message."""
    if RICH_AVAILABLE:
        console.print(Panel(
            "[bold cyan]CLaI - Command Line AI Assistant[/bold cyan]\n\n"
            "Type your questions or commands. I can execute shell commands to help you.\n"
            "Commands:\n"
            "  • [yellow]exit[/yellow] or [yellow]quit[/yellow] - Exit the program\n"
            "  • [yellow]/models[/yellow] - List available OpenRouter models\n"
            "  • [yellow]/clear[/yellow] - Clear conversation history",
            title="[bold]Welcome[/bold]",
            border_style="blue"
        ))
    else:
        print("\n=== CLaI - Command Line AI Assistant ===")
        print("Type your questions or commands. I can execute shell commands to help you.")
        print("Commands: exit, quit, /models, /clear\n")

def main():
    parser = argparse.ArgumentParser(description="Run the CLaI assistant")
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model to use (default: gpt-4o for OpenAI)",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "openrouter"],
        default="openai",
        help="API provider to use (default: openai)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available OpenRouter models and exit",
    )
    args = parser.parse_args()

    # Handle list-models command
    if args.list_models:
        list_openrouter_models()
        return

    # Check API keys
    if args.provider == "openai":
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            if RICH_AVAILABLE:
                console.print("[bold red]Error: OPENAI_API_KEY environment variable is not set[/bold red]")
            else:
                print("Error: OPENAI_API_KEY environment variable is not set")
            return
    else:  # openrouter
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_key:
            if RICH_AVAILABLE:
                console.print("[bold red]Error: OPENROUTER_API_KEY environment variable is not set[/bold red]")
            else:
                print("Error: OPENROUTER_API_KEY environment variable is not set")
            return

    print_welcome()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            if RICH_AVAILABLE:
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
            else:
                user_input = input("\nuser> ")
        except (EOFError, KeyboardInterrupt):
            if RICH_AVAILABLE:
                console.print("\n[yellow]Goodbye![/yellow]")
            else:
                print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            if RICH_AVAILABLE:
                console.print("[yellow]Goodbye![/yellow]")
            else:
                print("Goodbye!")
            break

        # Special commands
        if user_input == "/models":
            list_openrouter_models()
            continue

        if user_input == "/clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if RICH_AVAILABLE:
                console.print("[green]Conversation history cleared[/green]")
            else:
                print("Conversation history cleared")
            continue

        messages.append({"role": "user", "content": user_input})

        # Agent loop - keep calling API until no more tool calls
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                if args.provider == "openai":
                    message = call_openai_api(args.model, messages, TOOLS)
                else:
                    openrouter_key = os.getenv('OPENROUTER_API_KEY')
                    message = call_openrouter_api(args.model, messages, TOOLS, openrouter_key)

                # Convert message to dict if it's an object
                if hasattr(message, 'model_dump'):
                    message_dict = message.model_dump()
                elif hasattr(message, 'dict'):
                    message_dict = message.dict()
                else:
                    message_dict = message

                messages.append(message_dict)

                # Check for tool calls
                tool_calls = message_dict.get("tool_calls")

                if tool_calls:
                    for call in tool_calls:
                        if call.get("function", {}).get("name") == "run_shell":
                            try:
                                args_str = call.get("function", {}).get("arguments", "{}")
                                if isinstance(args_str, str):
                                    tool_args = json.loads(args_str)
                                else:
                                    tool_args = args_str

                                output = run_shell(tool_args.get("command", ""))

                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": call.get("id"),
                                    "content": output,
                                })
                            except json.JSONDecodeError as e:
                                error_msg = f"Error parsing tool arguments: {e}"
                                if RICH_AVAILABLE:
                                    console.print(f"[bold red]{error_msg}[/bold red]")
                                else:
                                    print(error_msg)
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": call.get("id"),
                                    "content": error_msg,
                                })
                    continue

                # No tool calls - print response and break
                content = message_dict.get("content")
                if content:
                    print_assistant_message(content)
                break

            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"[bold red]Error: {e}[/bold red]")
                else:
                    print(f"Error: {e}")
                break

        if iteration >= max_iterations:
            if RICH_AVAILABLE:
                console.print("[yellow]Warning: Maximum iterations reached[/yellow]")
            else:
                print("Warning: Maximum iterations reached")

if __name__ == "__main__":
    main()
