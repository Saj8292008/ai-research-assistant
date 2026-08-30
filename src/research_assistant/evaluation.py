from __future__ import annotations

import re
from dataclasses import dataclass

from .models import DraftBrief, Source

CITATION_PATTERN = re.compile(r"\[(S\d+)\]")
_WORD = re.compile(r"[a-z0-9]+")
_NEGATION = re.compile(
    r"\b(?:cannot|neither|never|no|nor|not|without)\b|n['’]t\b", re.IGNORECASE
)
_STOP = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "with",
}


@dataclass(frozen=True)
class EvaluationReport:
    citation_coverage: float
    unknown_citations: set[str]
    cited_source_ids: set[str]
    has_uncertainty: bool
    evidence_coverage: float = 0.0
    entailment_coverage: float = 0.0
    invalid_evidence: tuple[str, ...] = ()


def _claim_blocks(draft: DraftBrief) -> list[tuple[str, str]]:
    blocks = [("summary", draft.summary)] if draft.summary.strip() else []
    blocks.extend(
        (f"finding_{index}", text) for index, text in enumerate(draft.findings, 1) if text.strip()
    )
    return blocks


def _stem(word: str) -> str:
    if word.startswith("fail"):
        return "fail"
    for suffix in (
        "ingly",
        "edly",
        "ations",
        "ation",
        "ments",
        "ment",
        "ing",
        "ly",
        "ed",
        "es",
        "s",
    ):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _tokens(text: str) -> set[str]:
    cleaned = CITATION_PATTERN.sub("", text).lower()
    return {_stem(word) for word in _WORD.findall(cleaned) if word not in _STOP and len(word) > 1}


def _entailed(claim: str, quote: str) -> bool:
    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return False
    if bool(_NEGATION.search(claim)) != bool(_NEGATION.search(quote)):
        return False
    overlap = len(claim_tokens & _tokens(quote))
    ratio = overlap / len(claim_tokens)
    return overlap >= 2 and ratio >= 0.35


def _supports_part(claim: str, quote: str) -> bool:
    if bool(_NEGATION.search(claim)) != bool(_NEGATION.search(quote)):
        return False
    return len(_tokens(claim) & _tokens(quote)) >= 2


def evaluate_brief(draft: DraftBrief, sources: list[Source]) -> EvaluationReport:
    source_map = {source.id: source for source in sources}
    valid_ids = set(source_map)
    all_text = "\n".join([draft.summary, *draft.findings, *draft.uncertainty])
    cited_ids = set(CITATION_PATTERN.findall(all_text))
    blocks = _claim_blocks(draft)
    cited_blocks = sum(bool(CITATION_PATTERN.search(text)) for _, text in blocks)

    evidence_by_claim: dict[str, list] = {}
    for item in draft.evidence:
        evidence_by_claim.setdefault(item.claim_id, []).extend(item.spans)
    evidence_count = 0
    entailed_count = 0
    invalid = []
    for claim_id, claim in blocks:
        cited_for_claim = set(CITATION_PATTERN.findall(claim))
        valid_spans = 0
        valid_quotes = []
        valid_evidence_sources: set[str] = set()
        quotes_by_source: dict[str, list[str]] = {}
        for span in evidence_by_claim.get(claim_id, []):
            source = source_map.get(span.source_id)
            quote = span.quote.strip()
            if source is None:
                invalid.append(f"{claim_id}: unknown evidence source {span.source_id}")
            elif not quote:
                invalid.append(f"{claim_id}: empty evidence quote for {span.source_id}")
            elif span.source_id not in cited_for_claim:
                invalid.append(f"{claim_id}: evidence source {span.source_id} is not cited")
            elif quote not in source.content:
                invalid.append(f"{claim_id}: quote not found in {span.source_id}")
            else:
                valid_spans += 1
                valid_quotes.append(quote)
                valid_evidence_sources.add(span.source_id)
                quotes_by_source.setdefault(span.source_id, []).append(quote)
        if valid_evidence_sources:
            for source_id in sorted((cited_for_claim & valid_ids) - valid_evidence_sources):
                invalid.append(f"{claim_id}: cited source {source_id} has no valid evidence")
            for source_id, quotes in sorted(quotes_by_source.items()):
                if not _supports_part(claim, " ".join(quotes)):
                    invalid.append(f"{claim_id}: evidence from {source_id} does not support the claim")
        if valid_spans:
            evidence_count += 1
        if valid_quotes and _entailed(claim, " ".join(valid_quotes)):
            entailed_count += 1

    denominator = len(blocks)
    return EvaluationReport(
        citation_coverage=cited_blocks / denominator if denominator else 0.0,
        unknown_citations=cited_ids - valid_ids,
        cited_source_ids=cited_ids,
        has_uncertainty=any(item.strip() for item in draft.uncertainty),
        evidence_coverage=evidence_count / denominator if denominator else 0.0,
        entailment_coverage=entailed_count / denominator if denominator else 0.0,
        invalid_evidence=tuple(invalid),
    )
