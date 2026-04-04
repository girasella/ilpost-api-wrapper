# TODO — Future Enhancements

## RSS feed integration

Expose the latest content from Il Post via the public RSS feed.

**Feed URL:** `https://www.ilpost.it/feed`

**Feed facts (verified 2026-04-04):**
- Returns **68 items** (custom generator, not standard WordPress)
- Mixes all three content types in one stream:
  - Articles: `/YYYY/MM/DD/slug/` URLs — have `<category>` tags
  - Podcasts: `/episodes/slug/` URLs — no `<category>`
  - Newsletters: `/newsletter/<hash>/` URLs — no `<category>`
- `<dc:creator>` is always empty
- `<description>` contains HTML (with image) for articles, plain text for podcasts/newsletters

**Approach:**
1. Fetch and parse the RSS feed (`urllib` + `xml.etree.ElementTree`)
2. For each `<item>`, search the API using the **exact title in quotes** + `sort=NEWEST`, `hits=1`
3. Match the result by comparing `doc.link` to the RSS `<link>` — not just by position
4. On mismatch or no results, fall back to a partial `Document` built from RSS fields
5. Return a list of `Document` objects (same model everywhere)

**Why search instead of using RSS data directly:**
The RSS only provides basic fields. The search API adds `id`, `subscriber` (paywall flag),
`score`, `tags`, and enables chaining `fetch_content=True`.

**Title search reliability — known failure cases:**
Some titles will not match reliably via phrase search:

| Title pattern | Example | Problem |
|---|---|---|
| Generic/recurring | `"Le prime pagine di oggi"`, `"Celebripost"` | Too ambiguous — wrong article returned |
| Date-stamped | `"Peanuts 2026 aprile 04"`, `"Sabato 4 aprile"` | Date tokens break phrase match |
| Single word | `"Celebripost"` | Returns unrelated results |

**Fallback strategy:** when `doc.link != rss_link`, construct a minimal `Document`
from RSS fields directly (title, link, pubDate → timestamp, description → summary,
category from `<category>` if present). The `id`, `score`, `subscriber`, `tags`
fields will be absent/default — acceptable degradation.

**Parallel fetching:**
68 sequential API calls would be slow (~10–20s). Use `concurrent.futures.ThreadPoolExecutor`
(stdlib) with a bounded pool (e.g. 8 workers) to fetch in parallel.

**New method on `IlPostClient`:**
```python
def latest(
    self,
    *,
    count: int = 20,
    content_type: Optional[ContentType] = None,
    fetch_content: bool = False,
    workers: int = 8,
) -> list[Document]:
    ...
```

The `content_type` filter would pre-filter RSS items by URL pattern before searching,
avoiding unnecessary API calls for unwanted types.
