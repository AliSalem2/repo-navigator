import anthropic
import time
from rich.console import Console
from src.tools import _get, GITHUB_API

console = Console()

COMPARE_PROMPT = """You are a senior engineer comparing what a project's README claims against what the source code actually reveals.

You will be given:
1. An onboarding document produced by reading source code only
2. The project's actual README

Your job is to produce a "README vs Reality" section in markdown.

Focus on:
- Things the source code reveals that the README never mentions
- Patterns or gotchas that only appear in the code
- Things the README claims that are incomplete, misleading, or outdated based on the code
- Hidden complexity the README glosses over

Be specific and technical. Name actual files, classes, and functions.
Keep it concise — 5 to 8 bullet points maximum.

OUTPUT FORMAT:
## README vs reality

### What the source code reveals that the README doesn't mention
- ...

### What the README oversimplifies or skips
- ...
"""

def fetch_readme(owner: str, repo: str) -> str | None:
    for filename in ["README.md", "README.rst", "README.txt", "README"]:
        import base64
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{filename}"
        r = _get(url)
        if r.status_code == 200:
            data = r.json()
            if data.get("type") == "file":
                try:
                    content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                    lines = content.splitlines()
                    if len(lines) > 400:
                        content = "\n".join(lines[:400]) + f"\n\n[truncated — {len(lines)} total lines]"
                    return content
                except Exception:
                    return None
    return None

def compare_with_readme(owner: str, repo: str, onboarding_doc: str) -> str:
    console.print("[dim]Fetching README for comparison...[/dim]")
    readme = fetch_readme(owner, repo)

    if not readme:
        return "\n## README vs reality\n\n_No README found in this repository._\n"

    client = anthropic.Anthropic()

    user_message = f"""Here is the onboarding document produced from source code analysis:

<source_analysis>
{onboarding_doc}
</source_analysis>

Here is the actual README:

<readme>
{readme}
</readme>

Produce the README vs Reality section now."""

    for attempt in range(4):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                system=COMPARE_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            for block in response.content:
                if block.type == "text":
                    return "\n" + block.text
        except Exception as e:
            if "529" in str(e) and attempt < 3:
                wait = 10 * (attempt + 1)
                console.print(f"[yellow]API overloaded — retrying in {wait}s[/yellow]")
                time.sleep(wait)
            else:
                return "\n## README vs reality\n\n_Comparison unavailable due to API error._\n"

    return "\n## README vs reality\n\n_Comparison unavailable._\n"
