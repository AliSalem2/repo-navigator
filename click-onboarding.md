Now I have a comprehensive understanding of the Click codebase. Let me write the onboarding document.

## What this repo actually does

Click is a Python library for creating command-line interfaces (CLIs). It provides decorators and utilities to build complex command-line applications with options, arguments, subcommands, and interactive features. The library handles argument parsing, help text generation, input validation, terminal utilities (colors, prompts, progress bars), and testing infrastructure.

Core functionality includes:
- **Decorators** (`@click.command`, `@click.option`, `@click.argument`) that turn Python functions into CLI commands
- **Command grouping** to create multi-command applications with subcommands
- **Type system** with built-in types (INT, Path, Choice, etc.) and validation
- **Terminal UI utilities** for colors, prompts, progress bars, and pagination
- **Testing framework** (`CliRunner`) for testing CLI applications
- **Context management** for passing data between commands and handling configuration

## How to run it locally

```bash
# Clone and install in development mode
git clone https://github.com/pallets/click
cd click
pip install -e .

# Run tests
python -m pytest tests/

# Try examples
cd examples/complex
pip install -e .
complex --help
```

The library doesn't have a standalone executable - it's imported and used by other CLI applications. The examples directory contains working CLI applications that demonstrate usage patterns.

## Architecture: how the pieces connect

```
src/click/
├── __init__.py          # Public API exports
├── core.py              # Core classes (Command, Group, Context, Parameter)
├── decorators.py        # @click.command, @click.option decorators
├── types.py            # Parameter types (INT, Path, Choice, etc.)
├── parser.py           # Low-level argument parsing
├── utils.py            # echo(), file handling, utilities
├── termui.py          # Terminal UI (colors, prompts, progress bars)
├── testing.py         # CliRunner for testing
├── exceptions.py      # Click-specific exceptions
├── formatting.py      # Help text formatting
└── globals.py         # Global context management
```

**Data flow:**
1. Decorators (`@click.command`) create `Command` objects with attached `Parameter` objects
2. When invoked, `Command.main()` creates a `Context` and calls `Parser` to process argv
3. `Parser` uses `Parameter` objects to validate and convert arguments using `ParamType` classes
4. Parsed values are passed to the decorated function
5. `Context` provides shared state and configuration throughout the call chain

**Key relationships:**
- `Command` contains `Parameter` objects (options/arguments)
- `Group` is a `Command` that can contain other commands
- `Context` carries state and is accessible via `click.get_current_context()`
- All UI output goes through `click.echo()` for consistent handling

## Core files to read first (with one-line explanations)

1. `src/click/__init__.py` - Public API surface, shows what users import
2. `src/click/decorators.py` - Core decorators that users interact with daily
3. `src/click/core.py` - Command, Group, Context, Parameter base classes
4. `src/click/types.py` - Built-in parameter types and validation system
5. `src/click/utils.py` - echo() function and file handling utilities
6. `src/click/testing.py` - CliRunner for testing CLI applications
7. `examples/complex/complex/cli.py` - Real-world example showing patterns
8. `tests/test_basic.py` - Basic usage patterns and expected behavior

## Key patterns and conventions

**Decorator pattern**: Functions are transformed into CLI commands using `@click.command()` and enhanced with `@click.option()` and `@click.argument()`.

**Context passing**: Use `@click.pass_context` or `click.make_pass_decorator()` to share data between commands. Context objects are accessible via `click.get_current_context()`.

**Parameter types**: All inputs are validated through `ParamType` classes. Custom types inherit from `click.ParamType` and implement `convert()`.

**Error handling**: Click exceptions inherit from `ClickException` and are automatically formatted for users. Use `click.echo(err=True)` for stderr output.

**Testing pattern**: Use `CliRunner().invoke(command, args)` to test commands programmatically.

**Group commands**: Multi-command CLIs use `@click.group()` with subcommands registered via `@group.command()`.

**Dynamic command loading**: Groups can implement `list_commands()` and `get_command()` to load commands dynamically (see complex example).

**Environment variables**: Options automatically read from environment variables with `auto_envvar_prefix` or explicit `envvar` parameter.

## What is undocumented or surprising

**Three-state boolean logic**: Boolean flags have three states (True/False/None) when default is None, not just True/False.

**LazyFile**: Files are opened lazily via `LazyFile` wrapper, not immediately when parameter is processed.

**Context.meta**: Arbitrary data storage via `ctx.meta` dictionary is widely used internally but not well documented.

**Parser vs Core separation**: Low-level parsing in `parser.py` is separate from high-level command logic in `core.py`.

**ANSI color handling**: Complex logic for detecting terminal capabilities and stripping ANSI codes automatically.

**Type conversion caching**: Parameter types cache conversion results to avoid repeated validation.

**Testing isolation**: `CliRunner` captures stdout/stderr and provides isolated environment for testing.

**Callback execution order**: Option callbacks execute during parsing, not after all parsing is complete.

## Where to go next

**Start building**: Create a simple CLI with `@click.command()` and `@click.option()` decorators.

**Study examples**: Look at `examples/complex/` for advanced patterns like dynamic command loading and context sharing.

**Read tests**: `tests/test_*.py` files show expected behavior and edge cases.

**Custom types**: Implement `click.ParamType` subclasses for domain-specific validation.

**Advanced features**: Explore `termui.py` for progress bars, prompts, and colors.

**Testing**: Use `CliRunner` to write comprehensive tests for your CLI applications.

**Plugin patterns**: Study how Click groups can be extended and how commands can be dynamically loaded.
## README vs reality

### What the source code reveals that the README doesn't mention
- **Complex three-state boolean logic**: Boolean flags actually have three states (True/False/None) when default is None, not just simple True/False as the README implies
- **LazyFile implementation**: Files are opened lazily via `LazyFile` wrapper rather than immediately, which has implications for error handling and resource management
- **Extensive terminal UI utilities**: The codebase includes a full `termui.py` module with progress bars, prompts, colors, and pagination that the README never mentions
- **Built-in testing framework**: Click includes `CliRunner` class for testing CLI applications, which is a major feature completely absent from the README

### What the README oversimplifies or skips
- **Context management complexity**: The README doesn't explain the `Context` system (`click.get_current_context()`, `ctx.meta`, `@click.pass_context`) which is fundamental to advanced Click usage
- **Parameter type system**: No mention of the extensive type validation system with built-in types like `Path`, `Choice`, `IntRange` and the ability to create custom `ParamType` subclasses
- **Dynamic command loading**: While the README mentions "lazy loading of subcommands," it doesn't explain that groups can implement `list_commands()` and `get_command()` methods for runtime command discovery
- **Environment variable integration**: The automatic environment variable support via `auto_envvar_prefix` and `envvar` parameters is not documented in the README's basic example