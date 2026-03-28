# CLAUDE.md

## Project overview

Python wrapper library for the Il Post public search API.
Zero third-party dependencies — only the Python 3.9+ stdlib is used.

## Package layout

```
ilpost/
  __init__.py   — public exports
  client.py     — IlPostClient (all HTTP logic lives here)
  models.py     — dataclasses and enums (SearchResult, Document, SortOrder, …)
main.py         — CLI for manual testing
```

## Common commands

### Install (editable)
```bash
pip install -e .
```

### Run the CLI
```bash
python main.py <query> [options]
python main.py --help
```

### Run tests
```bash
pytest
```

### Lint / format
```bash
ruff check .
ruff format .
```

## Development guidelines

- **No external dependencies.** All HTTP calls use `urllib.request` from the stdlib.
- **Models are plain dataclasses.** Do not introduce Pydantic or attrs.
- The single HTTP entry point is `IlPostClient._get()` in [ilpost/client.py](ilpost/client.py). All new API methods must go through it.
- Enums (`SortOrder`, `ContentType`, `DateRange`) are the source of truth for API string values. Add new values there rather than using raw strings in method signatures.
- `IlPostClient.paginate()` is a generator — keep it lazy (no buffering all pages in memory).

## API reference

See [ilpost-search-api.md](ilpost-search-api.md) for the raw API documentation.
See [README.md](README.md) for the wrapper's public API.
