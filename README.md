# CLaI

CLaI is a command-line coding assistant that can run shell commands. It uses the
OpenAI API, so you need to set an `OPENAI_API_KEY` environment variable before
starting.

Run the assistant with:

```bash
python clai.py
```

You can specify a different model with `--model MODEL_NAME`.

Shell commands run by the assistant are echoed to the terminal so you can
see exactly what was executed and its output.

Type `exit` or `quit` to stop the session.
