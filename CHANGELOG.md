# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-04-02

### Fixed
- **Filter separator bug:** multiple filters were silently ignored because the separator
  was `,` instead of `;`. Only the first filter was ever applied by the server.
  Affects any call combining two or more of `content_type`, `category`, `date_range`.

### Added
- `category` parameter on `search()`, `search_articles()`, and `paginate()` now accepts
  a `list[str]` to AND multiple categories together (intersection logic).
- Query syntax guidance in `search()` docstring: documents `|` pipe OR operator, exact
  phrase search, and unsupported syntax (`title:`, `^`, `~N`).
- New "Known Limitations & Gotchas" section in `ilpost-search-api.md` based on
  API discovery testing.

---

## [0.2.0] - 2026-04-02

### Added
- `ilpost-search` CLI command installed as a package entry point — no longer requires
  running `python main.py` directly.
- MIT License file.
- PyPI-ready metadata in `pyproject.toml`: `authors`, `keywords`, `classifiers`,
  `[project.urls]`.
- `py.typed` marker (PEP 561) for type checker support.
- `README.md` with full API reference and usage examples.
- `CLAUDE.md` with project guidelines for AI-assisted development.

### Changed
- Migrated packaging from `setup.py` to `pyproject.toml` (PEP 517/621).
  Fixes pip deprecation warning for editable installs on pip 25+.
- CLI source moved from `main.py` to `ilpost/cli.py` (inside the package).
- Fixed `.gitignore` UTF-16 encoding issue that caused git to misinterpret
  the BOM as a wildcard, accidentally ignoring all untracked files.

---

## [0.1.0] - 2026-04-02

### Added
- Initial release.
- `IlPostClient` with `search()`, `search_articles()`, `search_podcasts()`,
  `search_newsletters()`, and `paginate()` methods.
- `SearchResult`, `Document`, `FilterGroup`, `FilterOption` dataclasses.
- `SortOrder`, `ContentType`, `DateRange` enums.
- Zero dependencies — stdlib `urllib` only.
