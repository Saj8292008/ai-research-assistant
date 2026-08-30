import pytest

from research_assistant.models import DraftBrief, Source
from research_assistant.pipeline import ResearchPipeline, ResearchResult


class FixedCollector:
    def collect(self, topic: str, limit: int) -> list[Source]:
        return [
            Source(
                "S1",
                "Primary study",
                "https://example.com/study",
                "Evidence A supports the finding.",
            ),
            Source(
                "S2",
                "Review",
                "https://example.com/review",
                "Evidence B supports the review finding.",
            ),
        ][:limit]


class FixedSynthesizer:
    def __init__(self, draft: DraftBrief):
        self.draft = draft

    def synthesize(self, topic: str, sources: list[Source]) -> DraftBrief:
        return self.draft


def test_pipeline_returns_verified_brief_with_citations():
    from research_assistant.models import ClaimEvidence, EvidenceSpan

    draft = DraftBrief(
        summary="Evidence A supports the finding [S1].",
        findings=["Evidence B supports the review finding [S2]."],
        uncertainty=["Only two sources were reviewed [S1][S2]."],
        evidence=[
            ClaimEvidence("summary", [EvidenceSpan("S1", "Evidence A supports the finding.")]),
            ClaimEvidence(
                "finding_1", [EvidenceSpan("S2", "Evidence B supports the review finding.")]
            ),
        ],
    )
    result = ResearchPipeline(FixedCollector(), FixedSynthesizer(draft)).run("test topic", 2)

    assert isinstance(result, ResearchResult)
    assert result.citations_valid is True
    assert result.cited_source_ids == {"S1", "S2"}
    assert "## Uncertainty" in result.markdown
    assert "## Evidence" in result.markdown
    assert "[S1]: https://example.com/study" in result.markdown
    assert "Evidence Inspector" in result.html


def test_pipeline_rejects_unknown_citation():
    draft = DraftBrief("Unsupported claim [S9].", [], ["Unknown [S9]."])

    with pytest.raises(ValueError, match="Unknown citation"):
        ResearchPipeline(FixedCollector(), FixedSynthesizer(draft)).run("test topic", 2)


def test_pipeline_requires_citations_in_summary_and_findings():
    draft = DraftBrief("No citation here.", ["Still no citation."], ["Limited evidence [S1]."])

    with pytest.raises(ValueError, match="must include at least one citation"):
        ResearchPipeline(FixedCollector(), FixedSynthesizer(draft)).run("test topic", 2)


def test_pipeline_rejects_missing_claim_evidence():
    draft = DraftBrief(
        "Evidence A supports the finding [S1].",
        ["Evidence B supports the review finding [S2]."],
        ["Limited evidence [S1][S2]."],
    )

    with pytest.raises(ValueError, match="exact evidence span"):
        ResearchPipeline(FixedCollector(), FixedSynthesizer(draft)).run("test topic", 2)


def test_pipeline_fails_when_no_sources_are_collected():
    class EmptyCollector:
        def collect(self, topic: str, limit: int) -> list[Source]:
            return []

    draft = DraftBrief("Anything [S1].", [], ["Anything [S1]."])
    with pytest.raises(RuntimeError, match="No usable sources"):
        ResearchPipeline(EmptyCollector(), FixedSynthesizer(draft)).run("test", 3)
