from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import replace

from .http_client import USER_AGENT
from .models import Source
from .ranking import rank_sources


def _http_get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def _fetch_metadata(http_get: Callable[[str], str], request_url: str) -> dict:
    client = getattr(http_get, "__self__", None)
    metadata = getattr(client, "metadata", None)
    if callable(metadata):
        result = metadata(request_url)
        return {
            "fetched_at": str(result.get("fetched_at", "")),
            "from_cache": bool(result.get("from_cache", False)),
        }
    return {}


def _validate(topic: str, limit: int) -> None:
    if not topic.strip():
        raise ValueError("Topic cannot be empty")
    if limit < 1 or limit > 10:
        raise ValueError("Source limit must be between 1 and 10")


def _strip_markup(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


class WikipediaCollector:
    def __init__(self, http_get: Callable[[str], str] = _http_get):
        self.http_get = http_get

    def collect(self, topic: str, limit: int = 3) -> list[Source]:
        _validate(topic, limit)
        query = urllib.parse.urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "srlimit": limit,
                "format": "json",
                "utf8": 1,
            }
        )
        results = (
            json.loads(self.http_get(f"https://en.wikipedia.org/w/api.php?{query}"))
            .get("query", {})
            .get("search", [])
        )
        sources = []
        for result in results[:limit]:
            title = result["title"]
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(
                title.replace(" ", "_"), safe=""
            )
            payload = json.loads(self.http_get(url))
            content = payload.get("extract", "").strip()
            page_url = payload.get("content_urls", {}).get("desktop", {}).get("page", "")
            if content and page_url.startswith("https://"):
                sources.append(
                    Source(
                        "",
                        payload.get("title", title),
                        page_url,
                        content,
                        source_type="wikipedia",
                        publisher="Wikipedia",
                        **_fetch_metadata(self.http_get, url),
                    )
                )
        return [replace(source, id=f"S{index}") for index, source in enumerate(sources, 1)]


class ArxivCollector:
    def __init__(self, http_get: Callable[[str], str] = _http_get):
        self.http_get = http_get

    def collect(self, topic: str, limit: int = 3) -> list[Source]:
        _validate(topic, limit)
        query = urllib.parse.urlencode(
            {
                "search_query": f"all:{topic}",
                "start": 0,
                "max_results": limit,
                "sortBy": "relevance",
            }
        )
        request_url = f"https://export.arxiv.org/api/query?{query}"
        root = ET.fromstring(self.http_get(request_url))
        ns = {"a": "http://www.w3.org/2005/Atom"}
        sources = []
        for entry in root.findall("a:entry", ns):

            def value(name: str, node=entry) -> str:
                return (node.findtext(f"a:{name}", default="", namespaces=ns) or "").strip()

            content = re.sub(r"\s+", " ", value("summary"))
            raw_url = value("id").replace("http://", "https://")
            if (
                content
                and raw_url.startswith("https://arxiv.org/abs/")
                and "withdrawn" not in content.lower()
            ):
                authors = tuple(
                    (node.findtext("a:name", default="", namespaces=ns) or "").strip()
                    for node in entry.findall("a:author", ns)
                )
                sources.append(
                    Source(
                        "",
                        re.sub(r"\s+", " ", value("title")),
                        raw_url,
                        content,
                        source_type="arxiv",
                        publisher="arXiv",
                        authors=tuple(a for a in authors if a),
                        published_at=value("published")[:10],
                        **_fetch_metadata(self.http_get, request_url),
                    )
                )
        return [replace(source, id=f"S{index}") for index, source in enumerate(sources, 1)]


class CrossrefCollector:
    def __init__(self, http_get: Callable[[str], str] = _http_get):
        self.http_get = http_get

    def collect(self, topic: str, limit: int = 3) -> list[Source]:
        _validate(topic, limit)
        query = urllib.parse.urlencode(
            {
                "query": topic,
                "rows": limit,
                "select": "title,URL,abstract,author,published,publisher",
            }
        )
        request_url = f"https://api.crossref.org/works?{query}"
        items = json.loads(self.http_get(request_url)).get("message", {}).get("items", [])
        sources = []
        for item in items:
            content = _strip_markup(item.get("abstract", ""))
            url = item.get("URL", "")
            title = next(iter(item.get("title", [])), "").strip()
            if not content or not title or not url.startswith("https://"):
                continue
            authors = tuple(
                " ".join(filter(None, [a.get("given", ""), a.get("family", "")])).strip()
                for a in item.get("author", [])
            )
            parts = item.get("published", {}).get("date-parts", [[]])[0]
            published = "-".join(str(value).zfill(2) for value in parts) if parts else ""
            sources.append(
                Source(
                    "",
                    title,
                    url,
                    content,
                    source_type="crossref",
                    publisher=item.get("publisher", "Crossref"),
                    authors=tuple(a for a in authors if a),
                    published_at=published,
                    **_fetch_metadata(self.http_get, request_url),
                )
            )
        return [replace(source, id=f"S{index}") for index, source in enumerate(sources, 1)]


class DataGovCollector:
    def __init__(self, http_get: Callable[[str], str] = _http_get):
        self.http_get = http_get

    def collect(self, topic: str, limit: int = 3) -> list[Source]:
        _validate(topic, limit)
        query = urllib.parse.urlencode({"q": topic, "rows": limit})
        request_url = f"https://catalog.data.gov/api/3/action/package_search?{query}"
        records = json.loads(self.http_get(request_url)).get("result", {}).get("results", [])
        sources = []
        for item in records:
            resources = item.get("resources") or []
            url = next(
                (
                    resource.get("url", "")
                    for resource in resources
                    if resource.get("url", "").startswith("https://")
                ),
                "",
            )
            content = _strip_markup(item.get("notes", ""))
            title = item.get("title", "").strip()
            if title and content and url:
                publisher = item.get("organization", {}).get("title", "U.S. Government")
                sources.append(
                    Source(
                        "",
                        title,
                        url,
                        content,
                        source_type="government",
                        publisher=publisher,
                        published_at=item.get("metadata_modified", "")[:10],
                        **_fetch_metadata(self.http_get, request_url),
                    )
                )
        return [replace(source, id=f"S{index}") for index, source in enumerate(sources, 1)]


class MultiSourceCollector:
    def __init__(self, collectors=None):
        self.collectors = collectors or [
            ArxivCollector(),
            CrossrefCollector(),
            DataGovCollector(),
            WikipediaCollector(),
        ]

    def collect(self, topic: str, limit: int = 5) -> list[Source]:
        _validate(topic, limit)
        candidates = []
        errors = []
        for collector in self.collectors:
            try:
                candidates.extend(collector.collect(topic, min(limit, 5)))
            except (
                RuntimeError,
                OSError,
                ValueError,
                KeyError,
                TypeError,
                AttributeError,
                ET.ParseError,
                json.JSONDecodeError,
            ) as exc:
                errors.append(f"{type(collector).__name__}: {exc}")
        if not candidates and errors:
            raise RuntimeError("All source collectors failed: " + "; ".join(errors))
        return rank_sources(topic, candidates, limit)
