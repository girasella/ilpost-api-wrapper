# TODO — Future Enhancements

## Date-archive scraping (`get_by_date`)

Fetch all articles published on a specific calendar date by scraping the date-archive pages on the website. This is the replacement for the original RSS-based `latest()` approach, which was dropped because the search API has a ~5 day indexing lag and the RSS feed requires fragile per-item API lookups.

**Archive URL pattern:**
- `https://www.ilpost.it/YYYY/MM/DD/` — first page (20 articles)
- `https://www.ilpost.it/YYYY/MM/DD/page/N/` — subsequent pages

**Archive page structure (verified 2026-04-09):**
Each article appears as an `<article>` element containing:
- `<a href="...">` — article URL
- `<time>` — publication date (format: `DD/MM/YYYY`)
- `<h2>` — title
- `<p>` — summary (may be empty)
- `<figure><img>` — thumbnail

CSS class names are hashed and change on deploy — parse by tag structure only.

**Too-recent guard:**
If the requested date is within the last ~5 days, raise a `ValueError` (the indexing lag
means the archive page may still be updating and results would be incomplete).
Exact threshold to be confirmed during implementation.

**New method on `IlPostClient`:**
```python
def get_by_date(
    self,
    date: datetime.date,
    *,
    fetch_content: bool = False,
) -> list[Document]:
    ...
```

Returns `Document` objects populated from scraped fields. Fields not available on the
archive page (`id`, `score`, `tags`, `highlight`) get sensible defaults (0 / empty).

**CLI:**
Add `--archive-date YYYY-MM-DD` argument (distinct from existing `--date`/`-d` which
controls the date-range filter for searches). If the date is too recent, print an error
and exit with a non-zero code.
