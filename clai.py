import os
import openai
import subprocess
import json
import argparse
import readline

openai.api_key = os.getenv('OPENAI_API_KEY')

def run_shell(command: str) -> str:
    """Execute a shell command and return its output."""
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
        print(result.stdout)
        return result.stdout
    except Exception as e:
        err = f"Error running command: {e}"
        print(err)
        return err

SYSTEM_PROMPT = (
    "You are CLaI, a command-line coding assistant running in a local shell. "
    "You can execute commands using the `run_shell` tool. "
    "Use it whenever you need to inspect the filesystem or run code, "
    "and explain what you are doing."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell command and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute in the shell",
                    }
                },
                "required": ["command"],
            },
        },
    }
]

def main():
    parser = argparse.ArgumentParser(description="Run the CLaI assistant")
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)",
    )
    args = parser.parse_args()

    if not openai.api_key:
        print("OPENAI_API_KEY environment variable is not set")
        return
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        try:
            user_input = input("user> ")
        except EOFError:
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break
        messages.append({"role": "user", "content": user_input})
        while True:
            response = openai.ChatCompletion.create(
                model=args.model,
                messages=messages,
                tools=TOOLS,
            )
            message = response.choices[0].message
            messages.append(message)
            if message.tool_calls:
                for call in message.tool_calls:
                    if call.function.name == "run_shell":
                        args = json.loads(call.function.arguments)
                        output = run_shell(args.get("command", ""))
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call.id,
                                "content": output,
                            }
                        )
                continue
            print(f"assistant> {message.content}")
            break

if __name__ == "__main__":
    main()
