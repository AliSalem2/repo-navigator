# HTTPX Onboarding Document

## What this repo actually does

HTTPX is a modern HTTP client library for Python 3 that provides both synchronous and asynchronous APIs. It's designed as a "next generation HTTP client" that offers a requests-like interface but with async support, HTTP/2, and better performance characteristics.

The library provides:
- Sync and async HTTP clients (`Client` and `AsyncClient`)
- A command-line HTTP client tool (like curl/httpie)
- Pluggable transport layer architecture
- Built-in support for HTTP/2, proxies, authentication, and streaming
- Rich response handling with automatic content decoding
- Comprehensive timeout and connection pooling configuration

## How to run it locally

From the source code analysis, HTTPX can be used in several ways:

**As a library:**
```python
import httpx

# Sync usage
response = httpx.get("https://httpbin.org/json")
print(response.json())

# Async usage
async with httpx.AsyncClient() as client:
    response = await client.get("https://httpbin.org/json")
    print(response.json())
```

**As a CLI tool:**
```bash
# Install with CLI dependencies
pip install 'httpx[cli]'

# Use the command line tool
python -m httpx GET https://httpbin.org/json
```

The CLI supports rich formatting, syntax highlighting, and many curl-like options for headers, auth, data, etc.

## Architecture: how the pieces connect

HTTPX follows a layered architecture:

1. **Public API Layer** (`_api.py`): Provides simple functions like `get()`, `post()` that create temporary clients
2. **Client Layer** (`_client.py`): `Client` and `AsyncClient` classes that manage sessions, cookies, and configuration  
3. **Transport Layer** (`_transports/`): Abstract base classes (`BaseTransport`, `AsyncBaseTransport`) with concrete implementations for different protocols
4. **Models Layer** (`_models.py`): Core `Request` and `Response` objects, plus `Headers` and `Cookies` collections
5. **Content Layer** (`_content.py`): Handles request/response body encoding/decoding and streaming
6. **Configuration** (`_config.py`): `Timeout`, `Proxy`, and SSL context management

The transport layer is pluggable - you can swap in different transports (HTTP/1.1, HTTP/2, mock, ASGI, WSGI) without changing client code. All transports implement the same `handle_request()` / `handle_async_request()` interface.

## Core files to read first

1. `__init__.py` - Public API exports and module structure
2. `_client.py` - Main Client classes with request/response lifecycle  
3. `_models.py` - Request/Response objects and HTTP primitives
4. `_transports/base.py` - Transport abstraction that everything builds on
5. `_config.py` - Timeout, SSL, and proxy configuration patterns
6. `_api.py` - Convenience functions that most users interact with first
7. `_main.py` - CLI implementation showing real-world usage patterns

## Key patterns and conventions

**Transport Abstraction**: All network I/O goes through pluggable transport classes. Sync transports implement `handle_request()`, async ones implement `handle_async_request()`.

**Context Managers**: Both clients and transports are context managers. Resources are properly cleaned up via `__enter__`/`__exit__` (sync) and `__aenter__`/`__aexit__` (async).

**Streaming by Default**: Responses use streaming by default - you must explicitly call `.read()` or similar to consume the body. This prevents accidental memory issues with large responses.

**Immutable Request/Response**: Once created, Request and Response objects are largely immutable. Modifications create new instances.

**Type Flexibility**: APIs accept multiple types (str/bytes, dict/list of tuples) and normalize them internally. For example, headers can be passed as dict, list of tuples, or Header object.

**Timeout Configuration**: Complex timeout handling with separate timeouts for connect, read, write, and connection pool operations.

**Error Hierarchy**: Rich exception hierarchy inheriting from base `HTTPError`, `RequestError`, etc. with specific errors for different failure modes.

## What is undocumented or surprising

**Transport Interface Complexity**: The transport layer expects very specific Request/Response object formats with byte-level headers and URL components. This isn't obvious from the high-level API.

**Stream Lifecycle**: Response streams must be explicitly closed or consumed. The `handle_request` docstring mentions this, but it's easy to miss and cause resource leaks.

**Header Case Sensitivity**: Headers are case-insensitive for access but preserve original case. HTTP/2 vs HTTP/1.1 have different header normalization rules.

**Authentication Warnings**: The `_config.py` shows deprecated cert handling with warnings, suggesting the SSL configuration API has evolved.

**CLI Dependencies**: The main CLI functionality is optional and gracefully degrades if CLI dependencies aren't installed, but this isn't obvious from the import structure.

**Encoding Detection**: Content encoding detection is quite sophisticated (see `_models.py`) but the fallback behavior isn't well documented in the code.

## Where to go next

1. **Start with `_api.py`** to understand the simple request functions
2. **Read `_client.py`** to understand session management and the full client lifecycle  
3. **Explore `_transports/`** directory to see different transport implementations
4. **Check `_auth.py`** for authentication patterns (BasicAuth, DigestAuth, etc.)
5. **Look at test files** (not analyzed here) to understand expected usage patterns
6. **Study `_exceptions.py`** to understand error handling patterns
7. **Examine streaming patterns** in `_content.py` for advanced use cases

The codebase is well-structured with clear separation of concerns. The transport abstraction makes it easy to extend, and the dual sync/async API provides good flexibility for different use cases.
## README vs reality

### What the source code reveals that the README doesn't mention

- **Transport abstraction complexity**: The README never mentions the pluggable transport layer (`_transports/`) that allows swapping HTTP/1.1, HTTP/2, WSGI, ASGI, and mock transports through a common `BaseTransport` interface
- **Streaming-by-default behavior**: Response bodies use streaming by default and must be explicitly consumed via `.read()` or similar methods - the README shows simple `.text` access without explaining the underlying stream lifecycle
- **Complex timeout configuration**: While "strict timeouts everywhere" is mentioned, the code reveals separate timeout controls for connect, read, write, and pool operations in `_config.py` that aren't explained
- **Header case preservation quirks**: Headers are case-insensitive for access but preserve original casing, with different normalization rules between HTTP/1.1 and HTTP/2 protocols

### What the README oversimplifies or skips

- **CLI dependency graceful degradation**: The README shows `pip install 'httpx[cli]'` but doesn't mention that the main library gracefully handles missing CLI dependencies and can function without them
- **Resource management requirements**: Both clients and transports are context managers that require proper cleanup, but the README examples don't show context manager usage patterns that prevent resource leaks
- **Authentication deprecation warnings**: The source code in `_config.py` shows deprecated SSL certificate handling with warnings, indicating the authentication API has evolved beyond what simple examples suggest
- **Content encoding sophistication**: The README mentions "Automatic Content Decoding" but the `_models.py` code reveals complex encoding detection with fallback behaviors that can affect performance and reliability