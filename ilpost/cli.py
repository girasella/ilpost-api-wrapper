import argparse
import sys

from .client import IlPostClient
from .models import SortOrder, ContentType, DateRange


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ilpost-search",
        description="Search Il Post articles, podcasts, and newsletters.",
    )

    parser.add_argument("query", help="Search term")

    parser.add_argument(
        "--type", "-t",
        dest="content_type",
        choices=["articles", "podcasts", "newsletters"],
        default=None,
        help="Filter by content type (default: all)",
    )
    parser.add_argument(
        "--sort", "-s",
        choices=["relevance", "newest", "oldest"],
        default="relevance",
        help="Sort order (default: relevance)",
    )
    parser.add_argument(
        "--date", "-d",
        dest="date_range",
        choices=["all", "year", "month"],
        default=None,
        help="Publication date filter: all / year (past 12 months) / month (past 30 days)",
    )
    parser.add_argument(
        "--category", "-c",
        nargs="+",
        default=None,
        metavar="CATEGORY",
        help="Editorial category filter (articles only). Pass one or more values for OR union, e.g. --category politica economia",
    )
    parser.add_argument(
        "--page", "-p",
        type=int,
        default=1,
        help="Page number, 1-based (default: 1)",
    )
    parser.add_argument(
        "--hits", "-n",
        type=int,
        default=10,
        help="Results per page (default: 10)",
    )
    parser.add_argument(
        "--all-pages",
        action="store_true",
        help="Fetch and print all pages (ignores --page)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of pages to fetch when using --all-pages",
    )
    parser.add_argument(
        "--fetch-content",
        action="store_true",
        help="Scrape and display the full article text (articles only)",
    )

    return parser


_SORT_MAP = {
    "relevance": SortOrder.RELEVANCE,
    "newest": SortOrder.NEWEST,
    "oldest": SortOrder.OLDEST,
}

_CTYPE_MAP = {
    "articles": ContentType.ARTICLES,
    "podcasts": ContentType.PODCASTS,
    "newsletters": ContentType.NEWSLETTERS,
}

_DATE_MAP = {
    "all": DateRange.ALL_TIME,
    "year": DateRange.PAST_YEAR,
    "month": DateRange.PAST_30_DAYS,
}

_TYPE_LABEL = {
    "post": "article",
    "episodes": "podcast",
    "newsletter": "newsletter",
}


def print_result(result, *, show_header: bool = True) -> None:
    if show_header:
        print(f'\nQuery: "{result.query}"  |  '
              f"Total: {result.total}  |  "
              f"Page: {result.page}/{result.total_pages}  |  "
              f"Sort: {result.sort}")
        print("-" * 72)

    if not result.docs:
        print("No results.")
        return

    for doc in result.docs:
        label = _TYPE_LABEL.get(doc.type, doc.type)
        print(f"  type     : {label}")
        if doc.category:
            print(f"  category : {doc.category}")
        print(f"  title    : {doc.title}")
        print(f"  link     : {doc.link}")
        print(f"  date     : {doc.timestamp}")
        print(f"  score    : {doc.score:.2f}")
        if doc.is_paywalled:
            print(f"  access   : subscribers only")
        if doc.summary:
            print(f"  summary  : {doc.summary}")
        if doc.content:
            print(f"  content  : {doc.content}")
        elif doc.highlight:
            snippet = doc.highlight.replace("<span>", ">>").replace("</span>", "<<")
            print(f"  excerpt  : ...{snippet}...")
        print()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    sort = _SORT_MAP[args.sort]
    content_type = _CTYPE_MAP.get(args.content_type)
    date_range = _DATE_MAP.get(args.date_range)

    client = IlPostClient()

    try:
        if args.all_pages:
            first = True
            for page_result in client.paginate(
                args.query,
                hits=args.hits,
                sort=sort,
                content_type=content_type,
                category=args.category,
                date_range=date_range,
                max_pages=args.max_pages,
                fetch_content=args.fetch_content,
            ):
                print_result(page_result, show_header=first)
                first = False
        else:
            result = client.search(
                args.query,
                page=args.page,
                hits=args.hits,
                sort=sort,
                content_type=content_type,
                category=args.category,
                date_range=date_range,
                fetch_content=args.fetch_content,
            )
            print_result(result)

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
