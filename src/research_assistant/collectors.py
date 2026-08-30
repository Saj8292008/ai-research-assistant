import json
import urllib.parse
import urllib.request
from collections.abc import Callable

from .models import Source

USER_AGENT = "ai-research-assistant/0.1 (educational project)"


def _http_get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8")


class WikipediaCollector:
    """Collect a deliberately small, inspectable set of Wikipedia summaries."""

    def __init__(self, http_get: Callable[[str], str] = _http_get):
        self.http_get = http_get

    def collect(self, topic: str, limit: int = 3) -> list[Source]:
        if not topic.strip():
            raise ValueError("Topic cannot be empty")
        if limit < 1 or limit > 5:
            raise ValueError("Source limit must be between 1 and 5")

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
        search_url = f"https://en.wikipedia.org/w/api.php?{query}"
        results = json.loads(self.http_get(search_url)).get("query", {}).get("search", [])

        sources: list[Source] = []
        for result in results[:limit]:
            title = result["title"]
            summary_url = (
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + urllib.parse.quote(title.replace(" ", "_"), safe="")
            )
            payload = json.loads(self.http_get(summary_url))
            content = payload.get("extract", "").strip()
            page_url = payload.get("content_urls", {}).get("desktop", {}).get("page", "")
            if content and page_url.startswith("https://"):
                sources.append(
                    Source(
                        id=f"S{len(sources) + 1}",
                        title=payload.get("title", title),
                        url=page_url,
                        content=content,
                    )
                )
        return sources
