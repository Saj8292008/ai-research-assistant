from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    url: str
    content: str


@dataclass(frozen=True)
class DraftBrief:
    summary: str
    findings: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
