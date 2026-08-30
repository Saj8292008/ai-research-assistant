import json

from research_assistant.collectors import ArxivCollector, CrossrefCollector, DataGovCollector


def test_arxiv_collector_normalizes_primary_source_metadata():
    feed = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.00001v2</id>
        <updated>2025-02-02T00:00:00Z</updated><published>2024-01-01T00:00:00Z</published>
        <title> Tool-using agents </title><summary> Agents call tools reliably. </summary>
        <author><name>Ada Researcher</name></author>
      </entry>
    </feed>"""

    sources = ArxivCollector(http_get=lambda _: feed).collect("tool agents", 1)

    assert sources[0].url == "https://arxiv.org/abs/2401.00001v2"
    assert sources[0].source_type == "arxiv"
    assert sources[0].publisher == "arXiv"
    assert sources[0].authors == ("Ada Researcher",)
    assert sources[0].published_at == "2024-01-01"
    assert sources[0].content_hash
    assert sources[0].id == "S1"


def test_arxiv_collector_preserves_cache_fetch_provenance():
    feed = """<feed xmlns="http://www.w3.org/2005/Atom"><entry>
    <id>http://arxiv.org/abs/2401.1v1</id><title>Agent tools</title>
    <summary>Agents use tools.</summary><published>2024-01-01T00:00:00Z</published>
    </entry></feed>"""

    class Client:
        def get(self, url):
            self.url = url
            return feed

        def metadata(self, url):
            assert url == self.url
            return {"fetched_at": "2025-01-02T03:04:05+00:00", "from_cache": True}

    source = ArxivCollector(http_get=Client().get).collect("agents", 1)[0]

    assert source.fetched_at == "2025-01-02T03:04:05+00:00"
    assert source.from_cache is True


def test_crossref_collector_rejects_records_without_abstracts():
    payload = {
        "message": {
            "items": [
                {"title": ["No evidence"], "URL": "https://doi.org/10.1/nope"},
                {
                    "title": ["Agent evidence"],
                    "URL": "https://doi.org/10.1/yes",
                    "abstract": "<jats:p>Agents use external tools.</jats:p>",
                    "author": [{"given": "Lin", "family": "Q"}],
                    "published": {"date-parts": [[2025, 3, 4]]},
                    "publisher": "Example Press",
                },
            ]
        }
    }

    sources = CrossrefCollector(http_get=lambda _: json.dumps(payload)).collect("agents", 2)

    assert len(sources) == 1
    assert sources[0].content == "Agents use external tools."
    assert sources[0].source_type == "crossref"
    assert sources[0].authors == ("Lin Q",)
    assert sources[0].id == "S1"


def test_data_gov_collector_returns_government_dataset_descriptions():
    payload = {
        "result": {
            "results": [
                {
                    "title": "Federal AI inventory",
                    "notes": "An official inventory of agency AI use cases.",
                    "organization": {"title": "General Services Administration"},
                    "metadata_modified": "2025-05-06T12:00:00",
                    "resources": [{"url": "https://catalog.data.gov/dataset/federal-ai"}],
                }
            ]
        }
    }

    source = DataGovCollector(http_get=lambda _: json.dumps(payload)).collect("AI", 1)[0]

    assert source.source_type == "government"
    assert source.publisher == "General Services Administration"
    assert source.url.startswith("https://")
    assert source.id == "S1"


def test_multisource_collector_isolates_a_malformed_provider():
    from research_assistant.collectors import MultiSourceCollector
    from research_assistant.models import Source

    class MalformedProvider:
        def collect(self, topic, limit):
            raise KeyError("schema changed")

    class GoodProvider:
        def collect(self, topic, limit):
            return [Source("", "Agent study", "https://example.com", "Agent evidence")]

    sources = MultiSourceCollector([MalformedProvider(), GoodProvider()]).collect("agent", 1)

    assert [source.title for source in sources] == ["Agent study"]
