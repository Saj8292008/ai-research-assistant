from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

USER_AGENT = "ai-research-assistant/0.2 (educational research agent)"


class CachedHttpClient:
    """Stdlib HTTP client with expiring disk cache, fetch metadata, and bounded retries."""

    def __init__(
        self,
        cache_dir: Path | str,
        *,
        opener: Callable = urllib.request.urlopen,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        retries: int = 3,
        timeout: int = 20,
        ttl_seconds: int = 86_400,
    ):
        self.cache_dir = Path(cache_dir).expanduser()
        self.opener = opener
        self.sleep = sleep
        self.clock = clock
        self.retries = retries
        self.timeout = timeout
        self.ttl_seconds = ttl_seconds
        self._metadata: dict[str, dict] = {}

    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.json"

    def metadata(self, url: str) -> dict:
        return dict(self._metadata.get(url, {}))

    def get(self, url: str) -> str:
        cache_path = self._cache_path(url)
        if cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                age = self.clock() - float(cached["fetched_timestamp"])
                if cached.get("url") == url and age <= self.ttl_seconds:
                    self._metadata[url] = {
                        "fetched_at": cached["fetched_at"],
                        "from_cache": True,
                    }
                    return str(cached["body"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
                pass

        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    text = response.read().decode("utf-8")
                fetched_timestamp = self.clock()
                fetched_at = datetime.fromtimestamp(fetched_timestamp, UTC).isoformat()
                payload = {
                    "url": url,
                    "fetched_at": fetched_at,
                    "fetched_timestamp": fetched_timestamp,
                    "body": text,
                }
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(payload), encoding="utf-8")
                self._metadata[url] = {"fetched_at": fetched_at, "from_cache": False}
                return text
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt + 1 < self.retries:
                    self.sleep(0.25 * (2**attempt))
        raise RuntimeError(
            f"HTTP request failed after {self.retries} attempts: {url}: {last_error}"
        )
