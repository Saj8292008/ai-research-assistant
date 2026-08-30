from research_assistant.evaluation import evaluate_brief
from research_assistant.models import DraftBrief, Source


def test_evaluation_scores_citation_coverage_and_validity():
    draft = DraftBrief(
        summary="Claim one [S1]. Claim two [S2].",
        findings=["Claim three [S1]."],
        uncertainty=["Evidence is limited [S1][S2]."],
    )
    sources = [
        Source("S1", "A", "https://example.com/a", "A"),
        Source("S2", "B", "https://example.com/b", "B"),
    ]

    report = evaluate_brief(draft, sources)

    assert report.unknown_citations == set()
    assert report.citation_coverage == 1.0
    assert report.has_uncertainty is True
