from __future__ import annotations

import urllib.request
from html.parser import HTMLParser
from typing import Optional


class ArticleScraper(HTMLParser):
    """Extract article body paragraphs from an Il Post article page.

    The article body lives inside ``<div id="singleBody">``. Only ``<p>``
    tags directly within that div are collected; ad/analytics divs are
    automatically ignored. "Leggi anche" cross-link paragraphs are filtered.

    After calling ``feed(html)``, read the result from ``.text``
    (``None`` if nothing was captured).
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_body: bool = False       # inside <div id="singleBody">
        self._body_depth: int = 0         # nesting depth inside that div
        self._in_para: bool = False        # inside a <p> within the body
        self._current_para: list[str] = []
        self._paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._in_body:
            if tag == "div" and dict(attrs).get("id") == "singleBody":
                self._in_body = True
                self._body_depth = 1
            return

        if tag == "div":
            self._body_depth += 1
        elif tag == "p":
            self._in_para = True
            self._current_para = []

    def handle_endtag(self, tag: str) -> None:
        if not self._in_body:
            return

        if tag == "div":
            self._body_depth -= 1
            if self._body_depth <= 0:
                self._in_body = False
        elif tag == "p" and self._in_para:
            self._in_para = False
            text = " ".join(self._current_para).strip()
            if text and not text.startswith("– Leggi anche"):
                self._paragraphs.append(text)
            self._current_para = []

    def handle_data(self, data: str) -> None:
        if self._in_para:
            stripped = data.strip()
            if stripped:
                self._current_para.append(stripped)

    @property
    def text(self) -> Optional[str]:
        if not self._paragraphs:
            return None
        return "\n\n".join(self._paragraphs)


_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def fetch_article_content(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch *url* and return the article body as plain text.

    Paragraphs are separated by double newlines. Returns ``None`` on any
    error rather than raising.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="replace")
    except Exception:
        return None

    try:
        parser = ArticleScraper()
        parser.feed(html)
        return parser.text
    except Exception:
        return None


class ArchivePageScraper(HTMLParser):
    """Extract article listings from an Il Post date-archive page.

    Parses ``<article>`` elements inside ``<main id="main-content">`` and
    collects link, title, summary, timestamp, and image for each item.

    After calling ``feed(html)``, read results from ``.items``
    (list of dicts, one per article).
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_main: bool = False
        self._in_article: bool = False
        self._link_captured: bool = False
        self._in_time: bool = False
        self._in_h2: bool = False
        self._in_p: bool = False
        self._current: dict = {}
        self.items: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        if tag == "main" and attrs_dict.get("id") == "main-content":
            self._in_main = True
            return

        if not self._in_main:
            return

        if tag == "article":
            self._in_article = True
            self._link_captured = False
            self._current = {"link": "", "timestamp": "", "title": "", "summary": "", "image": ""}
            return

        if not self._in_article:
            return

        if tag == "a" and not self._link_captured:
            href = attrs_dict.get("href", "")
            if href:
                self._current["link"] = href
                self._link_captured = True
        elif tag == "time":
            self._in_time = True
        elif tag == "h2":
            self._in_h2 = True
        elif tag == "p" and not self._in_p:
            self._in_p = True
        elif tag == "img" and not self._current["image"]:
            self._current["image"] = attrs_dict.get("src", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "main":
            self._in_main = False
            return

        if not self._in_main:
            return

        if tag == "article":
            if self._in_article and self._current.get("link"):
                self.items.append(self._current)
            self._in_article = False
            self._current = {}
            return

        if not self._in_article:
            return

        if tag == "time":
            self._in_time = False
        elif tag == "h2":
            self._in_h2 = False
        elif tag == "p":
            self._in_p = False

    def handle_data(self, data: str) -> None:
        if not self._in_article:
            return
        text = data.strip()
        if not text:
            return
        if self._in_time:
            self._current["timestamp"] = text
        elif self._in_h2:
            self._current["title"] += text
        elif self._in_p:
            self._current["summary"] += text


def fetch_archive_page(url: str, timeout: int = 10) -> list[dict]:
    """Fetch one page of a date-archive URL and return raw article dicts.

    Returns an empty list on any error (network, parsing, or empty page).
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="replace")
        parser = ArchivePageScraper()
        parser.feed(html)
        return parser.items
    except Exception:
        return []
