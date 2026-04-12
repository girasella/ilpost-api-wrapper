# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.5.1] - 2026-04-12

### Fixed
- **`get_by_date()` enrichment improvements:**
  - Added summary-keyword fallback search (up to 7 words, relevance-sorted) when
    title phrase queries fail to match.
  - Fixed corrupted apostrophes in title queries: archive page titles containing
    Windows-1252 `\x92` bytes (decoded as `\ufffd`) are now normalised to `'`
    before searching.
  - Fixed trailing punctuation in title and summary query tokens (e.g. `imprecisioni,`
    → `imprecisioni`).
  - Extracted `_clean_query_words()` helper used by both title and summary paths.
- **Additional skippable article types** recognised and excluded before enrichment:
  Peanuts comic strips, daily photo roundups, `le-prime-pagine-*` (newspaper
  front-page galleries), and meteo forecast articles
  (`title.startswith("Le previsioni meteo")`).

---

## [0.5.0] - 2026-04-11

### Added
- **`get_by_date(date, *, fetch_content=False)`:** new method on `IlPostClient` that
  returns all articles published on a given date by scraping the Il Post date-archive
  page (`https://www.ilpost.it/YYYY/MM/DD/`). All pages are fetched automatically
  (20 articles per page). Each article is enriched with API fields (id, tags, category,
  subscriber status, full timestamp) via a title-based search lookup. Articles that
  cannot be matched in the search index are excluded from the results. Closes #2.
- **`--archive-date YYYY-MM-DD` CLI flag:** fetches all articles published on a specific
  date. Supports `--fetch-content` and `--output-json` / `--output-dir`. Passing a date
  within the last 5 days raises an error (search index lag).
- Progress logging to stderr during `get_by_date()` (archive page fetching, per-article
  enrichment progress, final count).
- Tags (`post_tag_text`) are now displayed in CLI output.

### Changed
- `query` is now optional in the CLI — either a query or `--archive-date` must be provided.
- **`--output-json` / `--output-dir` flags** (previously unreleased, deferred from 0.4.x):
  suppresses stdout and writes results to a timestamped JSON file. The output path is
  printed to stdout for scripting. Closes #5.

---

## [0.4.2] - 2026-04-09

### Fixed
- **Multi-category filter now uses OR union instead of AND intersection:** passing
  `category=["scienza", "italia"]` previously generated `category:scienza;category:italia`,
  which the server interprets as AND (almost always empty). The correct syntax is
  `category:scienza,italia` (comma-separated values). Closes #6.

### Changed
- `--category` CLI flag now accepts multiple values for OR filtering:
  `ilpost-search cultivar --category scienza italia mondo`

---

## [0.4.1] - 2026-04-05

### Fixed
- **Content fetching skipped for `flashes` and `blog_post` articles:** `Document.is_article`
  only matched `type == "post"`, so `fetch_content=True` had no effect on `flashes` and
  `blog_post` documents. Both article types use the same `<div id="singleBody">` structure
  and are now included.

---

## [0.4.0] - 2026-04-02

### Added
- **Article content scraping:** new `fetch_content=False` parameter on `search()`,
  `search_articles()`, and `paginate()`. When `True`, the full article body is fetched
  by scraping the article URL and stored in `doc.content`. Only applies to article
  documents (`type == "post"`); podcasts and newsletters are unaffected.
- New `ilpost/scraper.py` module with `ArticleScraper` (stdlib `html.parser` subclass)
  and `fetch_article_content(url, timeout)` — exported from the package for direct use.
  Targets `<div id="singleBody">`, which is the consistent content container across all
  Il Post articles. Scraping errors are silently swallowed (`doc.content` stays `None`).
- `Document.content: Optional[str]` field — `None` by default, populated when
  `fetch_content=True`.
- `--fetch-content` flag on the `ilpost-search` CLI — displays the full article text
  in place of the highlight excerpt when content is available.

### Changed
- CLI output now uses labelled fields (`type`, `category`, `title`, `link`, `date`,
  `score`, `summary`, `access`, `content`/`excerpt`) for easier reading.

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
