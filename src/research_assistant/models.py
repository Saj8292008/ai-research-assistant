from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    url: str
    content: str
    source_type: str = "web"
    publisher: str = ""
    authors: tuple[str, ...] = ()
    published_at: str = ""
    retrieved_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    fetched_at: str = ""
    from_cache: bool = False
    content_hash: str = ""
    relevance_score: float = 0.0

    def __post_init__(self) -> None:
        if not self.fetched_at:
            object.__setattr__(self, "fetched_at", self.retrieved_at)
        if not self.content_hash:
            digest = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
            object.__setattr__(self, "content_hash", digest)


@dataclass(frozen=True)
class EvidenceSpan:
    source_id: str
    quote: str


@dataclass(frozen=True)
class ClaimEvidence:
    claim_id: str
    spans: list[EvidenceSpan] = field(default_factory=list)


@dataclass(frozen=True)
class DraftBrief:
    summary: str
    findings: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    evidence: list[ClaimEvidence] = field(default_factory=list)
