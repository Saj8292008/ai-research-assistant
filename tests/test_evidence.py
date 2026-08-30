from research_assistant.evaluation import evaluate_brief
from research_assistant.models import ClaimEvidence, DraftBrief, EvidenceSpan, Source


def test_evaluation_verifies_exact_evidence_and_entailment_independently():
    sources = [
        Source(
            "S1",
            "Study",
            "https://example.com",
            "Agents call external software tools to complete tasks.",
        )
    ]
    draft = DraftBrief(
        summary="Agents call external software tools [S1].",
        findings=["Agents use tools to complete tasks [S1]."],
        uncertainty=["Only one study was reviewed [S1]."],
        evidence=[
            ClaimEvidence("summary", [EvidenceSpan("S1", "Agents call external software tools")]),
            ClaimEvidence(
                "finding_1",
                [EvidenceSpan("S1", "Agents call external software tools to complete tasks.")],
            ),
        ],
    )

    report = evaluate_brief(draft, sources)

    assert report.evidence_coverage == 1.0
    assert report.invalid_evidence == ()
    assert report.entailment_coverage == 1.0


def test_evaluation_combines_multiple_spans_to_support_a_multi_part_claim():
    sources = [
        Source(
            "S1",
            "Study",
            "https://example.com",
            "Agents use tools for tasks. Reliability requires validation and recovery.",
        )
    ]
    draft = DraftBrief(
        "Agents use tools for tasks, while reliability requires validation and recovery in practice [S1].",
        [],
        ["One source [S1]."],
        [
            ClaimEvidence(
                "summary",
                [
                    EvidenceSpan("S1", "Agents use tools for tasks."),
                    EvidenceSpan("S1", "Reliability requires validation and recovery."),
                ],
            )
        ],
    )

    assert evaluate_brief(draft, sources).entailment_coverage == 1.0


def test_evaluation_accepts_supported_paraphrase_with_exact_quote():
    source = Source(
        "S1",
        "Study",
        "https://example.com",
        "The effect remained detectable even when predictions repeatedly failed.",
    )
    draft = DraftBrief(
        "AI predictions influenced decisions even after repeated failures [S1].",
        [],
        ["One study [S1]."],
        [
            ClaimEvidence(
                "summary",
                [
                    EvidenceSpan(
                        "S1",
                        "The effect remained detectable even when predictions repeatedly failed.",
                    )
                ],
            )
        ],
    )

    assert evaluate_brief(draft, [source]).entailment_coverage == 1.0


def test_evaluation_rejects_broad_claim_with_only_incidental_overlap():
    source = Source("S1", "Study", "https://example.com", "AI systems use tools.")
    draft = DraftBrief(
        "AI systems use tools and are proven safe, reliable, unbiased, autonomous, cheap, transparent, and legally compliant [S1].",
        [],
        ["One source [S1]."],
        [ClaimEvidence("summary", [EvidenceSpan("S1", "AI systems use tools.")])],
    )

    assert evaluate_brief(draft, [source]).entailment_coverage == 0.0


def test_evaluation_rejects_evidence_that_negates_the_claim():
    source = Source(
        "S1",
        "Trial",
        "https://example.com/trial",
        "Treatment did not reduce mortality in the trial.",
    )
    draft = DraftBrief(
        "Treatment reduced mortality in the trial [S1].",
        [],
        ["One trial was reviewed [S1]."],
        [
            ClaimEvidence(
                "summary",
                [EvidenceSpan("S1", "Treatment did not reduce mortality in the trial.")],
            )
        ],
    )

    assert evaluate_brief(draft, [source]).entailment_coverage == 0.0


def test_evaluation_aggregates_duplicate_claim_evidence_entries():
    source = Source("S1", "Study", "https://example.com", "Agents use tools. Tools require checks.")
    draft = DraftBrief(
        "Agents use tools that require checks [S1].",
        [],
        ["One source [S1]."],
        [
            ClaimEvidence("summary", [EvidenceSpan("S1", "Agents use tools.")]),
            ClaimEvidence("summary", [EvidenceSpan("S1", "Tools require checks.")]),
        ],
    )

    report = evaluate_brief(draft, [source])
    assert report.evidence_coverage == 1.0
    assert report.entailment_coverage == 1.0


def test_evaluation_requires_evidence_for_every_cited_source():
    sources = [
        Source("S1", "Study one", "https://example.com/1", "Agents use tools."),
        Source("S2", "Study two", "https://example.com/2", "Tools can fail."),
    ]
    draft = DraftBrief(
        "Agents use tools [S1][S2].",
        [],
        ["Two sources were reviewed [S1][S2]."],
        [ClaimEvidence("summary", [EvidenceSpan("S1", "Agents use tools.")])],
    )

    report = evaluate_brief(draft, sources)

    assert "summary: cited source S2 has no valid evidence" in report.invalid_evidence


def test_evaluation_rejects_unrelated_evidence_from_an_extra_citation():
    sources = [
        Source("S1", "Study one", "https://example.com/1", "Agents use tools."),
        Source("S2", "Study two", "https://example.com/2", "Bananas are yellow."),
    ]
    draft = DraftBrief(
        "Agents use tools [S1][S2].",
        [],
        ["Two sources were reviewed [S1][S2]."],
        [
            ClaimEvidence(
                "summary",
                [
                    EvidenceSpan("S1", "Agents use tools."),
                    EvidenceSpan("S2", "Bananas are yellow."),
                ],
            )
        ],
    )

    report = evaluate_brief(draft, sources)

    assert "summary: evidence from S2 does not support the claim" in report.invalid_evidence


def test_evaluation_rejects_empty_evidence_quote():
    source = Source("S1", "Study", "https://example.com/1", "Agents use tools.")
    draft = DraftBrief(
        "Agents use tools [S1].",
        [],
        ["One source was reviewed [S1]."],
        [ClaimEvidence("summary", [EvidenceSpan("S1", "")])],
    )

    report = evaluate_brief(draft, [source])

    assert "summary: empty evidence quote for S1" in report.invalid_evidence


def test_evaluation_rejects_quote_not_found_in_source():
    source = Source("S1", "Study", "https://example.com", "Actual source text.")
    draft = DraftBrief(
        "Invented statement [S1].",
        [],
        ["Limited [S1]."],
        [ClaimEvidence("summary", [EvidenceSpan("S1", "Fabricated quote")])],
    )

    report = evaluate_brief(draft, [source])

    assert report.invalid_evidence
    assert report.entailment_coverage == 0.0
