from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime

from .models import Source

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"a", "an", "and", "are", "do", "does", "how", "in", "of", "or", "the", "to", "what"}
_AUTHORITY = {"government": 0.35, "crossref": 0.30, "arxiv": 0.25, "wikipedia": 0.10, "web": 0.05}


def _tokens(text: str) -> set[str]:
    return {word for word in _WORD.findall(text.lower()) if word not in _STOP}


def _recency(published_at: str) -> float:
    if not published_at:
        return 0.0
    try:
        year = int(published_at[:4])
    except ValueError:
        return 0.0
    age = max(0, datetime.now(UTC).year - year)
    return max(0.0, 0.20 - min(age, 10) * 0.02)


def rank_sources(topic: str, sources: list[Source], limit: int) -> list[Source]:
    """Rank relevant candidates, then prefer diversity without admitting irrelevant evidence."""
    query = _tokens(topic)
    scored: list[tuple[Source, float]] = []
    for source in sources:
        document = _tokens(f"{source.title} {source.content}")
        topical = len(query & document) / max(len(query), 1)
        composite = (
            topical * 0.65
            + _AUTHORITY.get(source.source_type, 0.05)
            + _recency(source.published_at)
        )
        scored.append((replace(source, relevance_score=round(composite, 4)), topical))

    best_topical = max((topical for _, topical in scored), default=0.0)
    minimum = max(0.20, best_topical * 0.50)
    viable = [source for source, topical in scored if topical >= minimum]
    viable.sort(key=lambda item: (-item.relevance_score, item.title.lower()))

    selected: list[Source] = []
    seen_types: set[str] = set()
    for source in viable:
        if source.source_type not in seen_types:
            selected.append(source)
            seen_types.add(source.source_type)
            if len(selected) == limit:
                break
    if len(selected) < limit:
        remaining = [source for source in viable if source not in selected]
        selected.extend(remaining[: limit - len(selected)])
    return [replace(source, id=f"S{index}") for index, source in enumerate(selected, 1)]
