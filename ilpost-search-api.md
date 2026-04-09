# Il Post Search API — Documentation

> **Base endpoint:** `https://api.ilpost.org/search/api/site_search/`

---

## Overview

A public HTTP `GET` API that searches articles, podcast episodes, and newsletters published on [ilpost.it](https://www.ilpost.it). It is powered by Elasticsearch and requires no authentication. Parameters are passed as query string. The response is JSON.

---

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `qs` | string | Yes | — | The search term (e.g. `berlusconi`, `cacao`) |
| `pg` | integer | No | `1` | Page number (1-based). Combined with `hits` to paginate through results |
| `sort` | string | No | `default` | Sort order. See values below |
| `filters` | string | No | `""` | Active filters as a comma-separated list of `key:value` pairs (URL-encoded). Empty string means no filter |
| `hits` | integer | No | `10` | Number of results to return per page |

### `sort` parameter values

These values were verified directly through the website's UI sort dropdown:

| UI label | `sort` value | Description |
|----------|--------------|-------------|
| Rilevanti | `default` | Sort by relevance score (Elasticsearch scoring). Each result has a `score > 0` |
| Più recenti | `date_d` | Sort by date descending — most recent results first. Score is `0.0` |
| Più vecchi | `date_a` | Sort by date ascending — oldest results first. Score is `0.0` |

> When using `date_d` or `date_a`, Elasticsearch skips relevance scoring and all returned documents have `"score": 0.0`.

---

### `filters` parameter — format and values

Filters are passed as a URL-encoded string in the format `key:value`, with multiple filters separated by commas (`%2C`):

```
filters=key1%3Avalue1%2Ckey2%3Avalue2
```

i.e. `key1:value1,key2:value2` with `:` encoded as `%3A` and `,` as `%2C`.

#### Filter group: `ctype` — Content type (`multi: true`)

| Value | Description |
|-------|-------------|
| `articoli` | Articles and news posts |
| `podcast` | Podcast episodes |
| `newsletter` | Newsletter issues |

#### Filter group: `category` — Editorial category (`multi: true`, articles only)

Applies only when `ctype=articoli` is active (or when no `ctype` filter is set). When filtering by podcast or newsletter, this group is omitted from the response. Observed values (may vary by query):

`politica`, `italia`, `mondo`, `cultura`, `economia`, `sport`, `virgolette`, `rassegna`, `media`, `tv`, `libri`, `scienza`, `europa`, `internet`, `mini`, `consumismi`, `storie-idee`, `video`, `blog`

#### Filter group: `pub_date` — Publication date range (`multi: false` — exclusive, radio-style)

| Value | Description |
|-------|-------------|
| `da_sempre` | All time (entire archive) |
| `ultimo_anno` | Past 12 months |
| `ultimi_30_giorni` | Past 30 days |

#### Filter behavior notes

- `ctype` and `category` are marked `multi: true` in the response metadata. However, passing the same key twice (e.g. `ctype:articoli,ctype:podcast`) causes the server to apply only the first value.
- `pub_date` is exclusive (`multi: false`): only one value can be active at a time.
- `ctype` and `category` are cumulative (AND logic): using both narrows the result set.
- The `doc_count` values in filter options reflect the count within the currently active filter context — for example, if `pub_date:ultimi_30_giorni` is active, all `doc_count` values show counts scoped to the last 30 days.
- When `ctype:podcast` is active, the `category` filter group disappears from the response entirely (podcast episodes have no editorial category).

---

## Response Structure

```json
{
  "header": { ... },
  "total": 5775,
  "docs": [ ... ],
  "filters": [ ... ],
  "sort": "default",
  "hits": 10,
  "mode": "content"
}
```

### `header` object

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Always `"success"` on a valid response |
| `status` | integer | HTTP status code (`200`) |
| `search_time_ms` | string | Total search processing time |
| `search_e_time_ms` | string | Extended processing time |
| `es_took` | integer | Elasticsearch internal processing time in milliseconds |
| `result_type` | string | Always `"listing"` for search results |

### Root-level fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of matching results for the current query + filters |
| `docs` | array | Array of result documents (see below) |
| `filters` | array | Filter groups with counts and selection state (see below) |
| `sort` | string | The active sort value echoed back (`default`, `date_d`, or `date_a`) |
| `hits` | integer | Number of results returned per page, echoing the `hits` request parameter |
| `mode` | string | Always `"content"` |

---

## Document Object (`docs[]`)

The structure varies slightly by content type.

### Article (`"type": "post"`)

```json
{
  "id": 3548057,
  "subscriber": false,
  "category": "politica",
  "derived_info": {},
  "image": "https://www.ilpost.it/wp-content/uploads/2026/03/27/...",
  "post_tag_text": ["antonio tajani", "forza italia", "marina berlusconi"],
  "timestamp": "2026-03-27T16:53:52",
  "title": "Cosa sta succedendo dentro a Forza Italia",
  "link": "https://www.ilpost.it/2026/03/27/...",
  "type": "post",
  "score": 25.238773,
  "summary": "Sommovimenti provocati...",
  "highlight": {
    "content": "...Silvio <span>Berlusconi</span>..."
  }
}
```

### Podcast episode (`"type": "episodes"`)

```json
{
  "id": 2743376,
  "subscriber": false,
  "derived_info": {
    "episode": {
      "image": "https://www.ilpost.it/wp-content/uploads/...",
      "link": "https://www.ilpost.it/episodes/la-nutella-e-lempire-state-building/",
      "podcast_name": "cosa-c-entra"
    }
  },
  "image": "https://www.ilpost.it/wp-content/uploads/...",
  "timestamp": "2023-04-20T12:00:58",
  "title": "La Nutella e l'Empire State Building",
  "link": "https://www.ilpost.it/episodes/la-nutella-e-lempire-state-building/",
  "type": "episodes",
  "score": 23.449741,
  "summary": "...",
  "highlight": { "content": "...al <span>cacao</span>..." }
}
```

### Newsletter (`"type": "newsletter"`)

```json
{
  "id": 3548528,
  "subscriber": false,
  "derived_info": {
    "newsletter": {
      "name": "todo:name",
      "image": "todo:image"
    }
  },
  "image": "https://x.ilpost.it/imgproxy/...",
  "timestamp": "2026-03-27T00:00:00",
  "title": "Montecit. – C'è un governo che non c'è più",
  "link": "https://www.ilpost.it/newsletter/...",
  "type": "newsletter",
  "score": 4.7315617,
  "summary": "...",
  "highlight": { "content": "...Marina <span>Berlusconi</span>..." }
}
```

### Common document fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique content identifier |
| `subscriber` | boolean | `true` if content is paywalled (subscribers only); `false` if publicly accessible |
| `category` | string | Editorial category — present only on articles (`type: "post"`) |
| `image` | string | URL of the cover image |
| `timestamp` | string (ISO 8601) | Publication date and time (Italian timezone, no UTC offset) |
| `title` | string | Content title |
| `link` | string | Full URL to the content page |
| `type` | string | Content type: `"post"` (article), `"episodes"` (podcast), `"newsletter"` |
| `score` | float | Elasticsearch relevance score. Is `0.0` when sorting by date (`date_d` / `date_a`) |
| `summary` | string | Short excerpt or abstract |
| `highlight.content` | string | Text snippet with the search term wrapped in `<span>term</span>` for highlighting |
| `post_tag_text` | string[] | Tags associated with the content — present on articles only |
| `derived_info` | object | Type-specific extra data: for episodes → `episode.link`, `episode.image`, `episode.podcast_name`; for newsletters → `newsletter.name` and `newsletter.image` (currently placeholder values `"todo:name"` / `"todo:image"`) |

---

## `filters` Array

Describes all available filter groups, their options, result counts, and current selection state.

```json
[
  {
    "name": "ctype",
    "label": "Tipologia",
    "multi": true,
    "contents": [
      { "key": "articoli",   "doc_count": 5157, "label": "Articoli",   "selected": false },
      { "key": "podcast",    "doc_count": 363,  "label": "Podcast",    "selected": false },
      { "key": "newsletter", "doc_count": 255,  "label": "Newsletter", "selected": false }
    ]
  },
  {
    "name": "category",
    "label": "Categorie",
    "multi": true,
    "contents": [
      { "key": "politica", "doc_count": 1576, "label": "Politica", "selected": false },
      ...
    ]
  },
  {
    "name": "pub_date",
    "label": "Data Pubblicazione",
    "multi": false,
    "contents": [
      { "key": "da_sempre",        "doc_count": 5775, "label": "Tutti",        "selected": false },
      { "key": "ultimo_anno",      "doc_count": 160,  "label": "Ultimo anno",  "selected": false },
      { "key": "ultimi_30_giorni", "doc_count": 15,   "label": "Ultimo mese",  "selected": false }
    ]
  }
]
```

### `filters[]` fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Filter group key, used as the prefix in the `filters` parameter (e.g. `ctype`) |
| `label` | string | Human-readable group label |
| `multi` | boolean | `true` = multiple values can be selected (checkbox); `false` = exclusive selection (radio) |
| `contents[].key` | string | Value to use in the `filters` parameter (e.g. `articoli`, `politica`, `ultimo_anno`) |
| `contents[].label` | string | Human-readable option label |
| `contents[].doc_count` | integer | Number of results matching this option within the current query/filter context |
| `contents[].selected` | boolean | `true` if this filter option is currently active |

---

## Pagination

Navigate through pages using `pg` (1-based) together with `hits`:

- `hits` controls page size (default: `10`)
- `pg=1` → items 1 to `hits`
- `pg=2` → items `hits+1` to `2×hits`
- Total pages = `ceil(total / hits)`

---

## Example Requests

**Basic relevance search:**
```
GET https://api.ilpost.org/search/api/site_search/?qs=berlusconi&pg=1&sort=default&filters=
```

**Most recent articles only:**
```
GET https://api.ilpost.org/search/api/site_search/?qs=renzi&pg=1&sort=date_d&filters=ctype%3Aarticoli
```

**Oldest first, politics category, last 30 days:**
```
GET https://api.ilpost.org/search/api/site_search/?qs=berlusconi&pg=1&sort=date_a&filters=pub_date%3Aultimi_30_giorni%2Ccategory%3Apolitica
```

**Podcasts about "cacao", most recent:**
```
GET https://api.ilpost.org/search/api/site_search/?qs=cacao&pg=1&sort=date_d&filters=ctype%3Apodcast
```

**5 results per page, past year, page 2:**
```
GET https://api.ilpost.org/search/api/site_search/?qs=sicilia&pg=2&sort=default&filters=pub_date%3Aultimo_anno&hits=5
```

---

## Additional Notes

- **No authentication required** for public queries. Content with `"subscriber": true` is still returned in results (title, summary, highlight), but its full content requires an active subscription on ilpost.it.
- **Backend:** Elasticsearch. The `es_took` field in `header` reports the raw ES query time in milliseconds.
- **Term highlighting:** `highlight.content` contains raw HTML — the matched term is wrapped in `<span>term</span>`.
- **Date format:** timestamps follow ISO 8601 without a timezone offset; they correspond to Italian local time (CET in winter, CEST in summer).
- **CORS:** the API is accessible cross-origin from browsers (it is consumed directly by the ilpost.it frontend).
- **`sort=date` (legacy):** the API also accepts the undocumented value `date` (equivalent to `date_d`), but the official frontend always sends `date_d` or `date_a`.

---

## Known Limitations & Gotchas (discovery log 2026-03-30)

### Filter separator is `;` not `,`
Multiple filters must be separated by `;` (URL-encoded as `%3B`). Commas only apply the first filter silently.

```
filters=ctype%3Aarticoli%3Bpub_date%3Aultimo_anno   ✔ articles from last year
```

Filters within the same group use AND logic (intersection). Combining two `ctype:` values always returns 0 results since a document can only have one type.

### OR operator: `|` (pipe) works
The single pipe `|` is an undocumented but functional OR operator, equivalent to the keyword `OR`. Double pipe `||` falls back to AND.

```
fofi | berlusconi    ✔ same as: fofi OR berlusconi
fofi || berlusconi   ✗ behaves as AND
```

### What does NOT work

| Syntax | Example | Actual behaviour |
|--------|---------|-----------------|
| Field prefix | `title:fofi` | Treated as two AND-ed tokens `title` and `fofi` — inflates results |
| Boost operator | `berlusconi^10` | `^` stripped; `10` injected as a literal AND token |
| Proximity query | `"goffredo fofi"~5` | Inflates results; tighter window returns *more* hits than wider — broken |
| `ctype:blog_post` filter | `filters=ctype:blog_post` | Silently ignored — always 0 results |

### Exact phrase search works
```
"goffredo fofi"    ✔ returns only documents with that exact phrase
```

### API is GET-only
`POST`, `PUT`, and all other methods return `{"detail":"Method \"POST\" not allowed."}`.
The `Access-Control-Allow-Methods` header listing POST/PUT is a generic CORS header, not specific to this endpoint.

### `selected` field is unreliable for same-group multi-filters
When two filters from the same group are applied (e.g. two `category:` values), only the first shows `"selected": true` in the response, even though both are active.

### Search index has a ~5 day lag
The Elasticsearch index does not include articles published in the last ~5 days. Querying for very recent content returns no results. The search API is not suitable for retrieving the latest news.

As a workaround, date-archive pages on the website (`https://www.ilpost.it/YYYY/MM/DD/`) list all articles published on a given day and are updated in real time. These pages are paginated (20 articles per page) via `https://www.ilpost.it/YYYY/MM/DD/page/N/` and can be scraped to access recent content not yet indexed by the API.
