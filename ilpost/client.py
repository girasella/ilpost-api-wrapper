from __future__ import annotations

import datetime
import json
import sys
import urllib.request
from typing import Optional, Union
from urllib.parse import urlencode, quote

from .models import Document, SearchResult, SortOrder, ContentType, DateRange
from .scraper import fetch_article_content, fetch_archive_page

_BASE_URL = "https://api.ilpost.org/search/api/site_search/"
_ARCHIVE_BASE_URL = "https://www.ilpost.it"


def _doc_from_archive_item(item: dict) -> Document:
    link = item.get("link", "")
    doc_type = "flashes" if "/flashes/" in link else "post"
    raw_ts = item.get("timestamp", "")
    try:
        ts = datetime.datetime.strptime(raw_ts, "%d/%m/%Y").strftime("%Y-%m-%dT00:00:00")
    except ValueError:
        ts = raw_ts
    return Document(
        id=0,
        type=doc_type,
        title=item.get("title", "").strip(),
        link=link,
        timestamp=ts,
        summary=item.get("summary", "").strip(),
        image=item.get("image", ""),
        score=0.0,
        subscriber=False,
    )


def _enrich_doc_from_search(doc: Document, client: IlPostClient) -> None:
    """Try to fill missing API fields (id, tags, subscriber, etc.) via title search."""
    words = doc.title.split()
    queries = [f'"{doc.title}"']
    if len(words) > 6:
        queries.append(f'"{" ".join(words[:6])}"')
    for query in queries:
        try:
            result = client.search(query, hits=5, sort=SortOrder.NEWEST)
        except Exception:
            return
        for found in result.docs:
            if found.link.rstrip("/") == doc.link.rstrip("/"):
                doc.id = found.id
                doc.subscriber = found.subscriber
                doc.timestamp = found.timestamp
                doc.post_tag_text = found.post_tag_text
                if found.category:
                    doc.category = found.category
                doc.derived_info = found.derived_info
                return


def _build_filters(
    content_type: Optional[ContentType] = None,
    category: Optional[Union[str, list[str]]] = None,
    date_range: Optional[DateRange] = None,
) -> str:
    parts: list[str] = []
    if content_type is not None:
        parts.append(f"ctype:{content_type.value}")
    if category is not None:
        cats = [category] if isinstance(category, str) else category
        parts.append(f"category:{','.join(cats)}")
    if date_range is not None:
        parts.append(f"pub_date:{date_range.value}")
    return ";".join(parts)


class IlPostClient:
    """Thin wrapper around the Il Post public search API.

    Parameters
    ----------
    timeout:
        HTTP request timeout in seconds (default: 10).
    """

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def _enrich_docs(self, docs: list, fetch_content: bool) -> None:
        if not fetch_content:
            return
        for doc in docs:
            if doc.is_article:
                doc.content = fetch_article_content(doc.link, self.timeout)

    def _get(self, params: dict) -> dict:
        qs = urlencode(params, quote_via=quote)
        url = f"{_BASE_URL}?{qs}"
        with urllib.request.urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def search(
        self,
        query: str,
        *,
        page: int = 1,
        hits: int = 10,
        sort: Union[SortOrder, str] = SortOrder.RELEVANCE,
        content_type: Optional[ContentType] = None,
        category: Optional[Union[str, list[str]]] = None,
        date_range: Optional[DateRange] = None,
        filters: Optional[str] = None,
        fetch_content: bool = False,
    ) -> SearchResult:
        """Search Il Post content.

        Parameters
        ----------
        query:
            Search term. Supports:

            - Exact phrase: ``'"goffredo fofi"'``
            - Boolean OR: ``"fofi | berlusconi"`` (``|`` and ``OR`` both work)
            - Boolean AND: ``"fofi AND berlusconi"`` or just ``"fofi berlusconi"``
            - Boolean NOT: ``"berlusconi NOT fininvest"``

            The following syntax does **not** work and should be avoided:

            - Field prefix (``title:fofi``, ``content:fofi``) — treated as literal tokens
            - Boost operator (``berlusconi^10``) — the numeric value becomes a search token
            - Proximity queries (``"goffredo fofi"~5``) — inflates results unpredictably
        page:
            1-based page number (default: 1).
        hits:
            Results per page (default: 10).
        sort:
            Sort order. ``SortOrder.RELEVANCE`` (default), ``SortOrder.NEWEST``,
            or ``SortOrder.OLDEST``.
        content_type:
            Filter by content type: ``ContentType.ARTICLES``, ``ContentType.PODCASTS``,
            or ``ContentType.NEWSLETTERS``.
        category:
            Filter articles by editorial category. Pass a single string
            (e.g. ``"politica"``) or a list to OR multiple categories together
            (e.g. ``["cultura", "libri"]``). Only meaningful when
            ``content_type=ContentType.ARTICLES`` or no content type filter is set.
        date_range:
            Filter by publication date: ``DateRange.ALL_TIME``, ``DateRange.PAST_YEAR``,
            or ``DateRange.PAST_30_DAYS``.
        filters:
            Raw pre-encoded filter string (e.g. ``"ctype:articoli;pub_date:ultimo_anno"``).
            Filters are separated by ``;``. When provided, overrides ``content_type``,
            ``category``, and ``date_range``.

        Returns
        -------
        SearchResult
        """
        if filters is None:
            filters = _build_filters(content_type, category, date_range)

        sort_value = sort.value if isinstance(sort, SortOrder) else sort

        params = {
            "qs": query,
            "pg": page,
            "sort": sort_value,
            "filters": filters,
            "hits": hits,
        }

        data = self._get(params)
        result = SearchResult.from_dict(data, page=page, query=query)
        self._enrich_docs(result.docs, fetch_content)
        return result

    def search_articles(
        self,
        query: str,
        *,
        page: int = 1,
        hits: int = 10,
        sort: Union[SortOrder, str] = SortOrder.RELEVANCE,
        category: Optional[Union[str, list[str]]] = None,
        date_range: Optional[DateRange] = None,
        fetch_content: bool = False,
    ) -> SearchResult:
        """Search articles only. Convenience wrapper around :meth:`search`."""
        return self.search(
            query,
            page=page,
            hits=hits,
            sort=sort,
            content_type=ContentType.ARTICLES,
            category=category,
            date_range=date_range,
            fetch_content=fetch_content,
        )

    def search_podcasts(
        self,
        query: str,
        *,
        page: int = 1,
        hits: int = 10,
        sort: Union[SortOrder, str] = SortOrder.RELEVANCE,
        date_range: Optional[DateRange] = None,
    ) -> SearchResult:
        """Search podcast episodes only. Convenience wrapper around :meth:`search`."""
        return self.search(
            query,
            page=page,
            hits=hits,
            sort=sort,
            content_type=ContentType.PODCASTS,
            date_range=date_range,
        )

    def search_newsletters(
        self,
        query: str,
        *,
        page: int = 1,
        hits: int = 10,
        sort: Union[SortOrder, str] = SortOrder.RELEVANCE,
        date_range: Optional[DateRange] = None,
    ) -> SearchResult:
        """Search newsletter issues only. Convenience wrapper around :meth:`search`."""
        return self.search(
            query,
            page=page,
            hits=hits,
            sort=sort,
            content_type=ContentType.NEWSLETTERS,
            date_range=date_range,
        )

    def paginate(
        self,
        query: str,
        *,
        hits: int = 10,
        sort: Union[SortOrder, str] = SortOrder.RELEVANCE,
        content_type: Optional[ContentType] = None,
        category: Optional[Union[str, list[str]]] = None,
        date_range: Optional[DateRange] = None,
        max_pages: Optional[int] = None,
        fetch_content: bool = False,
    ):
        """Iterate over all pages of search results, yielding one :class:`SearchResult`
        per page.

        Parameters
        ----------
        max_pages:
            Stop after this many pages. ``None`` means iterate until exhausted.

        Yields
        ------
        SearchResult
        """
        page = 1
        while True:
            result = self.search(
                query,
                page=page,
                hits=hits,
                sort=sort,
                content_type=content_type,
                category=category,
                date_range=date_range,
                fetch_content=fetch_content,
            )
            yield result
            if not result.has_next_page:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1

    def get_by_date(
        self,
        date: datetime.date,
        *,
        fetch_content: bool = False,
    ) -> list[Document]:
        """Return all articles published on *date* by scraping the date-archive page.

        Each article is enriched with API fields (id, tags, subscriber status, etc.)
        via a title-based search lookup. If a match cannot be confirmed by URL comparison,
        the article is returned with partial data only.

        Parameters
        ----------
        date:
            The publication date to fetch. Must be at least 5 days in the past
            (the search index has a ~5 day lag; recent dates are rejected).
        fetch_content:
            If ``True``, scrape the full article body for each result.

        Returns
        -------
        list[Document]

        Raises
        ------
        ValueError
            If *date* is in the future or within the last 5 days.
        """
        today = datetime.date.today()
        if date > today:
            raise ValueError(f"date cannot be in the future: {date}")
        if (today - date).days < 5:
            raise ValueError(
                f"{date} is too recent — archive dates must be at least 5 days in the past"
            )

        base = f"{_ARCHIVE_BASE_URL}/{date.year:04d}/{date.month:02d}/{date.day:02d}"
        docs: list[Document] = []
        page = 1
        while True:
            url = f"{base}/" if page == 1 else f"{base}/page/{page}/"
            print(f"Fetching archive page {page}...", file=sys.stderr)
            items = fetch_archive_page(url, self.timeout)
            if not items:
                break
            docs.extend(_doc_from_archive_item(i) for i in items)
            page += 1

        print(f"Found {len(docs)} articles. Enriching from API...", file=sys.stderr)
        for i, doc in enumerate(docs, 1):
            print(f"  [{i}/{len(docs)}] {doc.title[:70]}", file=sys.stderr)
            _enrich_doc_from_search(doc, self)
        if fetch_content:
            print("Fetching article content...", file=sys.stderr)
        self._enrich_docs(docs, fetch_content)
        return docs
