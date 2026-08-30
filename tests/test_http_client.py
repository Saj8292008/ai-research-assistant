import json
import urllib.error

from research_assistant.http_client import CachedHttpClient


class Response:
    def __init__(self, body: bytes):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


def test_http_client_retries_then_caches_success_with_fetch_metadata(tmp_path):
    attempts = 0
    now = 1_700_000_000.0

    def opener(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise urllib.error.URLError("temporary")
        return Response(b"payload")

    client = CachedHttpClient(
        tmp_path,
        opener=opener,
        sleep=lambda _: None,
        retries=3,
        clock=lambda: now,
        ttl_seconds=60,
    )

    assert client.get("https://example.com/data") == "payload"
    first = client.metadata("https://example.com/data")
    assert first["from_cache"] is False
    assert first["fetched_at"] == "2023-11-14T22:13:20+00:00"

    assert client.get("https://example.com/data") == "payload"
    second = client.metadata("https://example.com/data")
    assert second["from_cache"] is True
    assert second["fetched_at"] == first["fetched_at"]
    assert attempts == 3

    cache_file = next(tmp_path.glob("*.json"))
    cached = json.loads(cache_file.read_text())
    assert cached["url"] == "https://example.com/data"
    assert cached["fetched_at"] == first["fetched_at"]


def test_http_client_refetches_expired_cache(tmp_path):
    now = [1_700_000_000.0]
    responses = iter([Response(b"old"), Response(b"fresh")])
    client = CachedHttpClient(
        tmp_path,
        opener=lambda request, timeout: next(responses),
        sleep=lambda _: None,
        clock=lambda: now[0],
        ttl_seconds=10,
    )

    assert client.get("https://example.com/data") == "old"
    now[0] += 11
    assert client.get("https://example.com/data") == "fresh"
    assert client.metadata("https://example.com/data")["from_cache"] is False
