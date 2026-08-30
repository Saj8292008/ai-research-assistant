import re
from dataclasses import dataclass

from .models import DraftBrief, Source

CITATION_PATTERN = re.compile(r"\[(S\d+)\]")


@dataclass(frozen=True)
class EvaluationReport:
    citation_coverage: float
    unknown_citations: set[str]
    cited_source_ids: set[str]
    has_uncertainty: bool


def _claim_blocks(draft: DraftBrief) -> list[str]:
    return [text for text in [draft.summary, *draft.findings] if text.strip()]


def evaluate_brief(draft: DraftBrief, sources: list[Source]) -> EvaluationReport:
    valid_ids = {source.id for source in sources}
    all_text = "\n".join([draft.summary, *draft.findings, *draft.uncertainty])
    cited_ids = set(CITATION_PATTERN.findall(all_text))
    blocks = _claim_blocks(draft)
    cited_blocks = sum(bool(CITATION_PATTERN.search(block)) for block in blocks)
    coverage = cited_blocks / len(blocks) if blocks else 0.0
    return EvaluationReport(
        citation_coverage=coverage,
        unknown_citations=cited_ids - valid_ids,
        cited_source_ids=cited_ids,
        has_uncertainty=bool([item for item in draft.uncertainty if item.strip()]),
    )
