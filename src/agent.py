import json
import time
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from src.tools import (
    TOOL_DEFINITIONS,
    parse_repo,
    list_directory,
    read_file,
    search_code,
)

console = Console()

SYSTEM_PROMPT = """You are a senior engineer performing a deep codebase analysis for a new team member.

Your job is to explore a GitHub repository by reading SOURCE CODE ONLY and produce an onboarding document.

STRICT RULES:
- Do NOT read README.md, CHANGELOG.md, LICENSE, or any .md/.rst documentation files.
- Do NOT read lock files (package-lock.json, poetry.lock, etc.) or build artifacts.
- ALWAYS start by listing the root directory to understand the structure.
- Read source files to understand what the code actually does — not what docs claim it does.
- Use search_code to find key patterns like entry points, core classes, and dependency injection.
- Stop after at most 20 tool calls. Be selective — quality over quantity.
- Read at most 2 files per turn. Prioritise depth over breadth.
- When you have enough to write a thorough onboarding doc, stop calling tools and write it.

OUTPUT FORMAT — produce a markdown document with exactly these sections:
## What this repo actually does
## How to run it locally
## Architecture: how the pieces connect
## Core files to read first (with one-line explanations)
## Key patterns and conventions
## What is undocumented or surprising
## Where to go next
"""

MAX_TOOL_CALLS = 14
MAX_RETRIES = 6
# Keep only the last N tool result turns in context to limit token usage
CONTEXT_WINDOW_TURNS = 8


def _create_with_retry(client, messages, system, tools):
    for attempt in range(MAX_RETRIES):
        try:
            kwargs = dict(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system,
                messages=messages,
            )
            if tools:
                kwargs["tools"] = tools
            return client.messages.create(**kwargs)
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < MAX_RETRIES - 1:
                wait = 15 * (attempt + 1)
                console.print(f"[yellow]API overloaded — retrying in {wait}s (attempt {attempt + 1}/{MAX_RETRIES})[/yellow]")
                time.sleep(wait)
            else:
                raise


def _trim_messages(messages: list) -> list:
    """Keep the first user message + last CONTEXT_WINDOW_TURNS assistant/user pairs."""
    if len(messages) <= 1 + (CONTEXT_WINDOW_TURNS * 2):
        return messages
    first = messages[:1]
    tail = messages[-(CONTEXT_WINDOW_TURNS * 2):]
    # make sure tail starts with an assistant turn
    while tail and tail[0]["role"] != "assistant":
        tail = tail[1:]
    return first + tail


def dispatch_tool(tool_name: str, tool_input: dict, owner: str, repo: str) -> str:
    if tool_name == "list_directory":
        result = list_directory(owner, repo, tool_input.get("path", ""))
    elif tool_name == "read_file":
        result = read_file(owner, repo, tool_input["path"])
    elif tool_name == "search_code":
        result = search_code(owner, repo, tool_input["query"])
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result)


def run_agent(repo_url: str) -> str:
    owner, repo = parse_repo(repo_url)
    client = anthropic.Anthropic()

    console.print(Panel(
        f"[bold]repo-navigator[/bold]\n[dim]{owner}/{repo}[/dim]",
        border_style="blue"
    ))

    messages = [
        {
            "role": "user",
            "content": (
                f"Analyse this repository and produce a complete onboarding document: "
                f"https://github.com/{owner}/{repo}\n\n"
                f"Remember: read source code only, not documentation files."
            )
        }
    ]

    tool_call_count = 0

    while True:
        trimmed = _trim_messages(messages)
        response = _create_with_retry(client, trimmed, SYSTEM_PROMPT, TOOL_DEFINITIONS)

        text_blocks = [b for b in response.content if b.type == "text"]
        tool_blocks = [b for b in response.content if b.type == "tool_use"]

        messages.append({"role": "assistant", "content": response.content})

        # no tool calls — agent is done
        if not tool_blocks or response.stop_reason == "end_turn":
            if text_blocks:
                return text_blocks[-1].text
            return "No output generated."

        # execute all tool calls
        tool_results = []
        for tool_block in tool_blocks:
            tool_call_count += 1
            label = Text()
            label.append(f"[{tool_call_count}/{MAX_TOOL_CALLS}] ", style="dim")
            label.append(tool_block.name, style="bold cyan")
            label.append(f"  {json.dumps(tool_block.input)}", style="dim")
            console.print(label)

            result_str = dispatch_tool(tool_block.name, tool_block.input, owner, repo)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result_str,
            })

        # tool_result must immediately follow tool_use
        messages.append({"role": "user", "content": tool_results})

        # hard cap — safe now that tool_results are appended
        if tool_call_count >= MAX_TOOL_CALLS:
            console.print(f"[yellow]Tool call limit reached ({MAX_TOOL_CALLS}). Requesting final output...[/yellow]")
            messages.append({
                "role": "user",
                "content": "You have used enough tool calls. Now write the complete onboarding document based on what you have learned."
            })
            trimmed = _trim_messages(messages)
            final = _create_with_retry(client, trimmed, SYSTEM_PROMPT, TOOL_DEFINITIONS)
            for b in final.content:
                if b.type == "text":
                    return b.text
            return "No output generated."
