from research_assistant.models import ClaimEvidence, DraftBrief, EvidenceSpan, Source
from research_assistant.rendering import render_inspection_html


def test_inspection_html_rejects_unsafe_source_url():
    source = Source("S1", "Study", "javascript:alert(1)", "Agents use tools.")
    draft = DraftBrief(
        "Agents use tools [S1].",
        [],
        ["One source [S1]."],
        [ClaimEvidence("summary", [EvidenceSpan("S1", "Agents use tools.")])],
    )

    output = render_inspection_html("Agents", draft, [source])

    assert "javascript:" not in output
    assert 'href="#"' in output


def test_inspection_html_places_claims_beside_escaped_evidence():
    source = Source(
        "S1", "Study <One>", "https://example.com/study", "Agents use tools.", publisher="Lab"
    )
    draft = DraftBrief(
        "Agents use tools [S1].",
        ["Tools extend action [S1]."],
        ["Evidence is limited [S1]."],
        [ClaimEvidence("summary", [EvidenceSpan("S1", "Agents use tools.")])],
    )

    html = render_inspection_html("Agents & tools", draft, [source])

    assert "Evidence Inspector" in html
    assert "Agents &amp; tools" in html
    assert "Study &lt;One&gt;" in html
    assert "Agents use tools." in html
    assert "https://example.com/study" in html


def test_inspection_html_exposes_source_provenance():
    source = Source(
        "S1",
        "Study",
        "https://example.com/study",
        "Agents use tools.",
        source_type="arxiv",
        publisher="arXiv",
        published_at="2025-01-02",
        fetched_at="2026-01-02T03:04:05+00:00",
        from_cache=True,
        relevance_score=0.8123,
    )
    draft = DraftBrief(
        "Agents use tools [S1].",
        [],
        ["One source [S1]."],
        [ClaimEvidence("summary", [EvidenceSpan("S1", "Agents use tools.")])],
    )

    output = render_inspection_html("Agents", draft, [source])

    assert "arxiv" in output
    assert "2025-01-02" in output
    assert "cache hit" in output
    assert "0.8123" in output
    assert source.content_hash in output
