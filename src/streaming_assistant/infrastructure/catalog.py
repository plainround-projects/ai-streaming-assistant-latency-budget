"""The help center on disk: page catalog, a lazily built BM25 index (so the cold start is real) and a query cache."""

from __future__ import annotations

import html
import json
import threading
import time
from collections import OrderedDict
from pathlib import Path

from streaming_assistant.domain.retrieval import Bm25Index, Hit, Section


class PageCatalog:
    """Loads `data/help_pages.json`: 30 pages with titled sections."""

    def __init__(self, path: Path) -> None:
        pages = json.loads(path.read_text(encoding="utf-8"))
        self._sections = [
            Section(page["page_id"], page["title"], section["anchor"], section["heading"], section["text"])
            for page in pages
            for section in page["sections"]
        ]
        self._by_ref = {section.ref: section for section in self._sections}
        self._pages = {page["page_id"]: page for page in pages}

    @property
    def sections(self) -> list[Section]:
        """Every section of every page."""
        return list(self._sections)

    def section(self, ref: str) -> Section | None:
        """The section a `page#anchor` ref names, or None."""
        return self._by_ref.get(ref)

    def page_html(self, page_id: str) -> str | None:
        """A page as HTML with an id on every section, so `#anchor` opens it at the cited section."""
        page = self._pages.get(page_id)
        if page is None:
            return None
        body = "".join(
            f'<section id="{html.escape(s["anchor"])}"><h2>{html.escape(s["heading"])}</h2><p>{html.escape(s["text"])}</p></section>'
            for s in page["sections"]
        )
        title = html.escape(page["title"])
        return (
            f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{title}</title><style>:target{{background:#fff3b0}}body{{font:16px/1.5 system-ui;max-width:42rem;margin:2rem auto;padding:0 1rem}}</style>"
            f"</head><body><h1>{title}</h1>{body}</body></html>"
        )


class LazyBm25Retriever:
    """Builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time."""

    def __init__(self, catalog: PageCatalog) -> None:
        self._catalog = catalog
        self._index: Bm25Index | None = None
        self._lock = threading.Lock()
        self.build_seconds: float | None = None

    def warm(self) -> None:
        """Build the index now."""
        with self._lock:
            if self._index is None:
                started = time.perf_counter()
                self._index = Bm25Index(self._catalog.sections)
                self.build_seconds = time.perf_counter() - started

    def search(self, query: str, limit: int = 3) -> list[Hit]:
        """Best sections first; the first call pays for building the index unless `warm` ran."""
        self.warm()
        assert self._index is not None
        return self._index.search(query, limit)


class CachingRetriever:
    """A small LRU cache in front of a retriever, keyed by the normalized query. Repeated questions skip the scoring."""

    def __init__(self, inner: LazyBm25Retriever, size: int = 512) -> None:
        self._inner = inner
        self._size = size
        self._cache: OrderedDict[tuple[str, int], list[Hit]] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def search(self, query: str, limit: int = 3) -> list[Hit]:
        """Cached hits for a repeated query."""
        key = (" ".join(query.lower().split()), limit)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self.hits += 1
                return list(self._cache[key])
        found = self._inner.search(query, limit)
        with self._lock:
            self.misses += 1
            self._cache[key] = found
            while len(self._cache) > self._size:
                self._cache.popitem(last=False)
        return list(found)
