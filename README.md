# ilpost-api-wrapper

A Python wrapper for the [Il Post](https://www.ilpost.it) public search API.
Searches articles, podcast episodes, and newsletters — no authentication required.

## Installation

```bash
pip install ilpost-api-wrapper
```

Requires Python 3.9+. No third-party dependencies.

## Quick start

```python
from ilpost import IlPostClient, SortOrder, ContentType, DateRange

client = IlPostClient()

result = client.search("berlusconi")
for doc in result.docs:
    print(doc.title, doc.link)
```

## API reference

### `IlPostClient(timeout=10)`

| Method | Description |
|--------|-------------|
| `search(query, ...)` | General search across all content types |
| `search_articles(query, ...)` | Articles only |
| `search_podcasts(query, ...)` | Podcast episodes only |
| `search_newsletters(query, ...)` | Newsletter issues only |
| `paginate(query, ...)` | Generator that yields one `SearchResult` per page |

#### Common parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Search term |
| `page` | `int` | `1` | Page number (1-based) |
| `hits` | `int` | `10` | Results per page |
| `sort` | `SortOrder` | `RELEVANCE` | Sort order |
| `content_type` | `ContentType` | `None` | Filter by content type |
| `category` | `str` | `None` | Editorial category (articles only) |
| `date_range` | `DateRange` | `None` | Publication date filter |

#### Enums

**`SortOrder`**
| Value | Description |
|-------|-------------|
| `RELEVANCE` | Sort by relevance score (default) |
| `NEWEST` | Most recent first |
| `OLDEST` | Oldest first |

**`ContentType`**
| Value | Description |
|-------|-------------|
| `ARTICLES` | Articles and news posts |
| `PODCASTS` | Podcast episodes |
| `NEWSLETTERS` | Newsletter issues |

**`DateRange`**
| Value | Description |
|-------|-------------|
| `ALL_TIME` | Entire archive (default) |
| `PAST_YEAR` | Past 12 months |
| `PAST_30_DAYS` | Past 30 days |

### `SearchResult`

| Attribute | Type | Description |
|-----------|------|-------------|
| `total` | `int` | Total number of matching results |
| `docs` | `list[Document]` | Results for this page |
| `filters` | `list[FilterGroup]` | Available filters with counts |
| `sort` | `str` | Active sort value |
| `hits` | `int` | Page size |
| `page` | `int` | Current page number |
| `total_pages` | `int` | Total number of pages |
| `has_next_page` | `bool` | Whether a next page exists |
| `has_prev_page` | `bool` | Whether a previous page exists |

### `Document`

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `int` | Unique content identifier |
| `type` | `str` | `"post"`, `"episodes"`, or `"newsletter"` |
| `title` | `str` | Content title |
| `link` | `str` | URL to the content page |
| `timestamp` | `str` | Publication date (ISO 8601, Italian local time) |
| `summary` | `str` | Short excerpt |
| `image` | `str` | Cover image URL |
| `score` | `float` | Relevance score (`0.0` when sorting by date) |
| `subscriber` | `bool` | `True` if content is paywalled |
| `highlight` | `str \| None` | Snippet with matched term in `<span>` tags |
| `category` | `str \| None` | Editorial category (articles only) |
| `post_tag_text` | `list[str]` | Tags (articles only) |
| `derived_info` | `dict` | Extra data: episode or newsletter metadata |
| `is_article` | `bool` | Convenience property |
| `is_podcast` | `bool` | Convenience property |
| `is_newsletter` | `bool` | Convenience property |
| `is_paywalled` | `bool` | Alias for `subscriber` |

## Examples

```python
from ilpost import IlPostClient, SortOrder, ContentType, DateRange

client = IlPostClient()

# Most recent articles in politics
result = client.search_articles(
    "renzi",
    sort=SortOrder.NEWEST,
    category="politica",
    date_range=DateRange.PAST_30_DAYS,
)

# Podcast search
result = client.search_podcasts("cacao", sort=SortOrder.NEWEST)

# Paginate through all results, 5 per page
for page in client.paginate("sicilia", hits=5, max_pages=10):
    print(f"Page {page.page}/{page.total_pages}")
    for doc in page.docs:
        print(f"  [{doc.type}] {doc.title}")

# Access filter counts from a response
result = client.search("europa")
for group in result.filters:
    print(f"{group.label}:")
    for opt in group.options:
        print(f"  {opt.label}: {opt.doc_count}")
```

## CLI

A command-line interface is provided via `main.py`:

```
usage: ilpost-search [-h] [--type {articles,podcasts,newsletters}]
                     [--sort {relevance,newest,oldest}]
                     [--date {all,year,month}] [--category CATEGORY]
                     [--page PAGE] [--hits HITS] [--all-pages]
                     [--max-pages N]
                     query
```

```bash
# Basic search
python main.py berlusconi

# Most recent articles in politics
python main.py renzi --type articles --sort newest --category politica

# Podcast search, past 30 days
python main.py cacao --type podcasts --date month

# Page 2, 5 results per page, oldest first
python main.py sicilia --sort oldest --hits 5 --page 2

# Fetch all pages of newsletter results (up to 3 pages)
python main.py economia --type newsletters --all-pages --max-pages 3
```

## Notes

- Paywalled content (`subscriber: true`) is included in search results — title, summary, and highlight are visible, but the full article requires an active ilpost.it subscription.
- When sorting by date (`NEWEST` or `OLDEST`), `score` is always `0.0`.
- The `category` filter only applies to articles. It is ignored by the server when `content_type=PODCASTS`.
- Timestamps are in Italian local time (CET/CEST) with no UTC offset.
