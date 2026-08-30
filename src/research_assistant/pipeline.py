from dataclasses import dataclass
from typing import Protocol

from .evaluation import evaluate_brief
from .models import DraftBrief, Source


class Collector(Protocol):
    def collect(self, topic: str, limit: int) -> list[Source]: ...


class Synthesizer(Protocol):
    def synthesize(self, topic: str, sources: list[Source]) -> DraftBrief: ...


@dataclass(frozen=True)
class ResearchResult:
    markdown: str
    citations_valid: bool
    cited_source_ids: set[str]
    source_count: int


def _render(topic: str, draft: DraftBrief, sources: list[Source]) -> str:
    findings = "\n".join(f"- {finding}" for finding in draft.findings)
    uncertainty = "\n".join(f"- {item}" for item in draft.uncertainty)
    references = "\n".join(
        f"[{source.id}]: {source.url} \"{source.title}\"" for source in sources
    )
    return (
        f"# Research Brief: {topic}\n\n"
        f"## Summary\n\n{draft.summary}\n\n"
        f"## Key Findings\n\n{findings}\n\n"
        f"## Uncertainty\n\n{uncertainty}\n\n"
        f"## Sources\n\n{references}\n"
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

        return ResearchResult(
            markdown=_render(topic, draft, sources),
            citations_valid=True,
            cited_source_ids=report.cited_source_ids,
            source_count=len(sources),
        )
