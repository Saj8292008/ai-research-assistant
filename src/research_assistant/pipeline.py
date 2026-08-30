from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .evaluation import EvaluationReport, evaluate_brief
from .models import DraftBrief, Source
from .rendering import render_inspection_html


class Collector(Protocol):
    def collect(self, topic: str, limit: int) -> list[Source]: ...


class Synthesizer(Protocol):
    def synthesize(self, topic: str, sources: list[Source]) -> DraftBrief: ...


@dataclass(frozen=True)
class ResearchResult:
    markdown: str
    html: str
    citations_valid: bool
    cited_source_ids: set[str]
    source_count: int
    evaluation: EvaluationReport


def _render(topic: str, draft: DraftBrief, sources: list[Source]) -> str:
    findings = "\n".join(f"- {finding}" for finding in draft.findings)
    uncertainty = "\n".join(f"- {item}" for item in draft.uncertainty)
    source_map = {source.id: source for source in sources}
    evidence_lines = []
    for item in draft.evidence:
        for span in item.spans:
            source = source_map.get(span.source_id)
            if source:
                evidence_lines.append(f"- **{item.claim_id} — [{span.source_id}]**: “{span.quote}”")
    evidence = "\n".join(evidence_lines)
    references = "\n".join(
        f'[{source.id}]: {source.url} "{source.title}" — '
        f"{source.publisher or source.source_type}; published {source.published_at or 'unknown'}; "
        f"remote fetched {source.fetched_at}; cache {'hit' if source.from_cache else 'miss'}; "
        f"run observed {source.retrieved_at}; sha256 `{source.content_hash}`; "
        f"rank {source.relevance_score:.4f}"
        for source in sources
    )
    return (
        f"# Research Brief: {topic}\n\n"
        f"## Summary\n\n{draft.summary}\n\n"
        f"## Key Findings\n\n{findings}\n\n"
        f"## Evidence\n\n{evidence}\n\n"
        f"## Uncertainty\n\n{uncertainty}\n\n"
        f"## Sources and Provenance\n\n{references}\n"
    )


class ResearchPipeline:
    def __init__(self, collector: Collector, synthesizer: Synthesizer):
        self.collector = collector
        self.synthesizer = synthesizer

    def run(self, topic: str, source_limit: int = 3) -> ResearchResult:
        sources = self.collector.collect(topic, source_limit)
        if not sources:
            raise RuntimeError("No usable sources were collected")

        draft = self.synthesizer.synthesize(topic, sources)
        report = evaluate_brief(draft, sources)
        if report.unknown_citations:
            unknown = ", ".join(sorted(report.unknown_citations))
            raise ValueError(f"Unknown citation(s): {unknown}")
        if report.citation_coverage < 1.0:
            raise ValueError("Every summary and finding must include at least one citation")
        if not report.has_uncertainty:
            raise ValueError("Brief must include an uncertainty section")
        if report.invalid_evidence:
            raise ValueError("Invalid evidence: " + "; ".join(report.invalid_evidence))
        if report.evidence_coverage < 1.0:
            raise ValueError("Every summary and finding must include an exact evidence span")
        if report.entailment_coverage < 1.0:
            raise ValueError("At least one evidence span must lexically support every claim")

        return ResearchResult(
            markdown=_render(topic, draft, sources),
            html=render_inspection_html(topic, draft, sources),
            citations_valid=True,
            cited_source_ids=report.cited_source_ids,
            source_count=len(sources),
            evaluation=report,
        )
