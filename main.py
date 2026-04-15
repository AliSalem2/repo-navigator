import click
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from src.agent import run_agent
from src.tools import parse_repo
from src.compare import compare_with_readme

load_dotenv()
console = Console()

@click.command()
@click.option("--repo", required=True, help="GitHub repo URL e.g. https://github.com/owner/repo")
@click.option("--output", default=None, help="Save output to a markdown file")
@click.option("--compare", is_flag=True, default=False, help="Append a README vs reality section")
def main(repo: str, output: str, compare: bool):
    """repo-navigator — understand any codebase without reading the docs."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY not set.[/red]")
        raise SystemExit(1)

    result = run_agent(repo)

    if compare:
        owner, repo_name = parse_repo(repo)
        comparison = compare_with_readme(owner, repo_name, result)
        result = result + comparison

    console.print("\n")
    console.print(Markdown(result))

    if output:
        with open(output, "w") as f:
            f.write(result)
        console.print(f"\n[green]Saved to {output}[/green]")

if __name__ == "__main__":
    main()
