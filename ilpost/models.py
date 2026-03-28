from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SortOrder(str, Enum):
    RELEVANCE = "default"
    NEWEST = "date_d"
    OLDEST = "date_a"


class ContentType(str, Enum):
    ARTICLES = "articoli"
    PODCASTS = "podcast"
    NEWSLETTERS = "newsletter"


class DateRange(str, Enum):
    ALL_TIME = "da_sempre"
    PAST_YEAR = "ultimo_anno"
    PAST_30_DAYS = "ultimi_30_giorni"


@dataclass
class FilterOption:
    key: str
    label: str
    doc_count: int
    selected: bool

    @classmethod
    def from_dict(cls, data: dict) -> FilterOption:
        return cls(
            key=data["key"],
            label=data["label"],
            doc_count=data["doc_count"],
            selected=data["selected"],
        )


@dataclass
class FilterGroup:
    name: str
    label: str
    multi: bool
    options: list[FilterOption]

    @classmethod
    def from_dict(cls, data: dict) -> FilterGroup:
        return cls(
            name=data["name"],
            label=data["label"],
            multi=data["multi"],
            options=[FilterOption.from_dict(c) for c in data.get("contents", [])],
        )


@dataclass
class Document:
    id: int
    type: str
    title: str
    link: str
    timestamp: str
    summary: str
    image: str
    score: float
    subscriber: bool
    highlight: Optional[str] = None
    category: Optional[str] = None
    post_tag_text: list[str] = field(default_factory=list)
    derived_info: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> Document:
        return cls(
            id=data["id"],
            type=data["type"],
            title=data["title"],
            link=data["link"],
            timestamp=data["timestamp"],
            summary=data.get("summary", ""),
            image=data.get("image", ""),
            score=data.get("score", 0.0),
            subscriber=data.get("subscriber", False),
            highlight=data.get("highlight", {}).get("content"),
            category=data.get("category"),
            post_tag_text=data.get("post_tag_text", []),
            derived_info=data.get("derived_info", {}),
        )

    @property
    def is_article(self) -> bool:
        return self.type == "post"

    @property
    def is_podcast(self) -> bool:
        return self.type == "episodes"

    @property
    def is_newsletter(self) -> bool:
        return self.type == "newsletter"

    @property
    def is_paywalled(self) -> bool:
        return self.subscriber


@dataclass
class SearchResult:
    total: int
    docs: list[Document]
    filters: list[FilterGroup]
    sort: str
    hits: int
    page: int
    query: str

    @classmethod
    def from_dict(cls, data: dict, page: int, query: str) -> SearchResult:
        return cls(
            total=data["total"],
            docs=[Document.from_dict(d) for d in data.get("docs", [])],
            filters=[FilterGroup.from_dict(f) for f in data.get("filters", [])],
            sort=data.get("sort", "default"),
            hits=data.get("hits", 10),
            page=page,
            query=query,
        )

    @property
    def total_pages(self) -> int:
        if self.hits == 0:
            return 0
        return -(-self.total // self.hits)  # ceiling division

    @property
    def has_next_page(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev_page(self) -> bool:
        return self.page > 1
