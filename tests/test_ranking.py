from research_assistant.models import Source
from research_assistant.ranking import rank_sources


def test_ranking_does_not_force_irrelevant_source_for_diversity():
    sources = [
        Source(
            "",
            "Agent tools",
            "https://arxiv.org/1",
            "Agents use external tools reliably",
            source_type="arxiv",
        ),
        Source(
            "",
            "Tool validation",
            "https://arxiv.org/2",
            "Agent tools need validation and recovery",
            source_type="arxiv",
        ),
        Source(
            "",
            "Weather",
            "https://catalog.data.gov/weather",
            "Temperature and rainfall records",
            source_type="government",
        ),
    ]

    ranked = rank_sources("agent external tools reliability", sources, limit=3)

    assert [source.title for source in ranked] == ["Agent tools", "Tool validation"]


def test_ranking_prefers_relevant_authoritative_sources_and_preserves_diversity():
    sources = [
        Source(
            "x",
            "AI agents",
            "https://arxiv.org/abs/1",
            "AI agents call software tools",
            source_type="arxiv",
            published_at="2026-01-01",
        ),
        Source(
            "x",
            "AI agents survey",
            "https://doi.org/2",
            "AI agents use tools",
            source_type="crossref",
            published_at="2025-01-01",
        ),
        Source(
            "x",
            "Federal AI",
            "https://catalog.data.gov/x",
            "Government AI agent inventory and tools",
            source_type="government",
            published_at="2025-06-01",
        ),
        Source(
            "x",
            "Cooking",
            "https://arxiv.org/abs/3",
            "Recipes and kitchens",
            source_type="arxiv",
            published_at="2026-01-01",
        ),
    ]

    ranked = rank_sources("How do AI agents use tools?", sources, limit=3)

    assert [source.id for source in ranked] == ["S1", "S2", "S3"]
    assert {source.source_type for source in ranked} == {"arxiv", "crossref", "government"}
    assert all(source.relevance_score > 0 for source in ranked)
    assert "Cooking" not in {source.title for source in ranked}


def test_ranking_supports_symbol_heavy_topics():
    sources = [
        Source("", "C++ safety", "https://example.com/cpp", "C++ memory safety guidance"),
        Source("", "Cooking", "https://example.com/food", "Recipes and kitchens"),
    ]

    ranked = rank_sources("C++", sources, limit=2)

    assert [source.title for source in ranked] == ["C++ safety"]
