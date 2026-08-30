import json

from research_assistant.collectors import WikipediaCollector


def test_wikipedia_collector_turns_api_results_into_sources():
    calls: list[str] = []

    def fake_get(url: str) -> str:
        calls.append(url)
        if "list=search" in url:
            return json.dumps({"query": {"search": [{"title": "Agentic AI"}]}})
        return json.dumps(
            {
                "title": "Agentic AI",
                "extract": "Agentic AI systems pursue goals using tools.",
                "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Agentic_AI"}},
            }
        )

    sources = WikipediaCollector(http_get=fake_get).collect("agentic AI", limit=1)

    assert len(sources) == 1
    assert sources[0].id == "S1"
    assert sources[0].title == "Agentic AI"
    assert sources[0].url.startswith("https://")
    assert "pursue goals" in sources[0].content
    assert len(calls) == 2
