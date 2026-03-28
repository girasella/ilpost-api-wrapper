from __future__ import annotations

from typing import Optional, Union
from urllib.parse import urlencode, quote

import urllib.request
import json

from .models import SearchResult, SortOrder, ContentType, DateRange

_BASE_URL = "https://api.ilpost.org/search/api/site_search/"


def _build_filters(
    content_type: Optional[ContentType] = None,
    category: Optional[str] = None,
    date_range: Optional[DateRange] = None,
) -> str:
    parts: list[str] = []
    if content_type is not None:
        parts.append(f"ctype:{content_type.value}")
    if category is not None:
        parts.append(f"category:{category}")
    if date_range is not None:
        parts.append(f"pub_date:{date_range.value}")
    return ",".join(parts)


class IlPostClient:
    """Thin wrapper around the Il Post public search API.

    Parameters
    ----------
    timeout:
        HTTP request timeout in seconds (default: 10).
    """

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

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
        category: Optional[str] = None,
        date_range: Optional[DateRange] = None,
        filters: Optional[str] = None,
    ) -> SearchResult:
        """Search Il Post content.

        Parameters
        ----------
        query:
            Search term.
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
            Filter articles by editorial category (e.g. ``"politica"``, ``"cultura"``).
            Only meaningful when ``content_type=ContentType.ARTICLES`` or no content
            type filter is set.
        date_range:
            Filter by publication date: ``DateRange.ALL_TIME``, ``DateRange.PAST_YEAR``,
            or ``DateRange.PAST_30_DAYS``.
        filters:
            Raw pre-encoded filter string (e.g. ``"ctype:articoli,pub_date:ultimo_anno"``).
            When provided, overrides ``content_type``, ``category``, and ``date_range``.

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
        return SearchResult.from_dict(data, page=page, query=query)

    def search_articles(
        self,
        query: str,
        *,
        page: int = 1,
        hits: int = 10,
        sort: Union[SortOrder, str] = SortOrder.RELEVANCE,
        category: Optional[str] = None,
        date_range: Optional[DateRange] = None,
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
        category: Optional[str] = None,
        date_range: Optional[DateRange] = None,
        max_pages: Optional[int] = None,
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
            )
            yield result
            if not result.has_next_page:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1
