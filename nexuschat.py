#!/usr/bin/env python3
"""
NEXUS Chat — Terminal AI chatbot with multi-provider routing (Groq, Gemini,
OpenRouter) and persistent SQLite history.

Setup:
    pip install -r requirements.txt
    Set whichever provider keys you have, e.g.:
        export GROQ_API_KEY="your_key_here"
        export GEMINI_API_KEY="your_key_here"
        export OPENROUTER_API_KEY="your_key_here"
    (or put them in a .env file next to this script)

Run:
    python nexuschat.py

Commands (type inside chat):
    /new                 start a new conversation
    /sessions            list saved conversations
    /load <id>           resume a saved conversation
    /rename <title>      rename current conversation
    /provider <name>     switch provider: groq | gemini | openrouter
    /model <name>        switch model within the current provider
    /models              list suggested models for the current provider
    /clear                clear the screen
    /exit                quit
"""

import os
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

import db
import providers

console = Console()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_PROMPT = (
    "You are NEXUS, a helpful terminal-based AI assistant running on the "
    "user's device via Termux. Keep answers clear and concise unless asked "
    "for detail."
)

DEFAULT_PROVIDER = "groq"


def print_banner(provider, model):
    console.print(
        Panel(
            f"[bold cyan]NEXUS Chat[/] — terminal AI\n"
            f"[dim]Provider:[/] [bold]{providers.PROVIDERS[provider]['label']}[/]  "
            f"[dim]Model:[/] [bold]{model}[/]\n"
            "[dim]Type /exit to quit, /sessions to see saved chats, /provider to switch AI[/]",
            border_style="cyan",
        )
    )


def show_sessions():
    convs = db.list_conversations()
    if not convs:
        console.print("[yellow]No saved conversations yet.[/]")
        return
    for c in convs:
        console.print(f"[bold]{c['id']}[/]  {c['title']}  [dim]{c['created_at']}[/]")


def show_models(provider):
    console.print(f"[cyan]Suggested models for {providers.PROVIDERS[provider]['label']}:[/]")
    for m in providers.PROVIDERS[provider]["suggested_models"]:
        console.print(f"  - {m}")
    console.print("[dim]You can also use any other model name the provider supports.[/]")


def pick_starting_provider():
    """Use the first provider that has a key available; fall back to groq."""
    for name in [DEFAULT_PROVIDER] + [p for p in providers.PROVIDERS if p != DEFAULT_PROVIDER]:
        if providers.load_key(name, SCRIPT_DIR):
            return name
    return DEFAULT_PROVIDER


def main():
    db.init_db()

    provider = pick_starting_provider()
    api_key = providers.load_key(provider, SCRIPT_DIR)
    if not api_key:
        console.print(
            "[bold red]No API key found for any provider.[/] Set at least one of:\n"
            '  export GROQ_API_KEY="your_key_here"\n'
            '  export GEMINI_API_KEY="your_key_here"\n'
            '  export OPENROUTER_API_KEY="your_key_here"\n'
            "or create a .env file next to this script."
        )
        sys.exit(1)

    model = providers.PROVIDERS[provider]["default_model"]
    print_banner(provider, model)

    conv_id = db.create_conversation()
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Bye![/]")
            break

        if not user_input.strip():
            continue

        if user_input.startswith("/"):
            parts = user_input.strip().split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "/exit":
                console.print("[yellow]Bye![/]")
                break
            elif cmd == "/new":
                conv_id = db.create_conversation()
                history = [{"role": "system", "content": SYSTEM_PROMPT}]
                console.print(f"[green]Started new conversation (id={conv_id})[/]")
            elif cmd == "/sessions":
                show_sessions()
            elif cmd == "/load":
                try:
                    conv_id = int(arg)
                    saved = db.get_messages(conv_id)
                    if not saved:
                        console.print("[red]No such conversation.[/]")
                        continue
                    history = [{"role": "system", "content": SYSTEM_PROMPT}] + saved
                    console.print(f"[green]Loaded conversation {conv_id}[/]")
                except ValueError:
                    console.print("[red]Usage: /load <id>[/]")
            elif cmd == "/rename":
                if arg:
                    db.rename_conversation(conv_id, arg)
                    console.print(f"[green]Renamed to '{arg}'[/]")
                else:
                    console.print("[red]Usage: /rename <new title>[/]")
            elif cmd == "/provider":
                if not arg:
                    console.print(
                        f"[cyan]Current provider: {provider}[/]  "
                        f"(available: {', '.join(providers.PROVIDERS)})"
                    )
                elif arg not in providers.PROVIDERS:
                    console.print(f"[red]Unknown provider. Choose from: {', '.join(providers.PROVIDERS)}[/]")
                else:
                    new_key = providers.load_key(arg, SCRIPT_DIR)
                    if not new_key:
                        console.print(
                            f"[red]No API key found for {arg}.[/] "
                            f"Set {providers.PROVIDERS[arg]['env_key']} first."
                        )
                    else:
                        provider = arg
                        api_key = new_key
                        model = providers.PROVIDERS[provider]["default_model"]
                        console.print(
                            f"[green]Switched to {providers.PROVIDERS[provider]['label']} "
                            f"(model: {model})[/]"
                        )
            elif cmd == "/model":
                if arg:
                    model = arg
                    console.print(f"[green]Model switched to {model}[/]")
                else:
                    console.print(f"[cyan]Current model: {model}[/]")
            elif cmd == "/models":
                show_models(provider)
            elif cmd == "/clear":
                console.clear()
                print_banner(provider, model)
            else:
                console.print("[red]Unknown command.[/]")
            continue

        history.append({"role": "user", "content": user_input})
        db.add_message(conv_id, "user", user_input)

        try:
            with console.status(f"[cyan]NEXUS ({providers.PROVIDERS[provider]['label']}) is thinking...[/]"):
                reply = providers.call(provider, api_key, model, history)
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")
            continue

        history.append({"role": "assistant", "content": reply})
        db.add_message(conv_id, "assistant", reply)

        console.print("[bold magenta]NEXUS[/]")
        console.print(Markdown(reply))


if __name__ == "__main__":
    main()
