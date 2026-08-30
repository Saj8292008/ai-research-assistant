import json
import re
import subprocess
from collections.abc import Callable

from .models import ClaimEvidence, DraftBrief, EvidenceSpan, Source


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.DOTALL)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("Hermes did not return a JSON object") from None
        return json.loads(cleaned[start : end + 1])


class HermesSynthesizer:
    """Use the installed Hermes Agent CLI as the reasoning/synthesis layer."""

    def __init__(
        self,
        run_command: Callable = subprocess.run,
        timeout: int = 180,
        provider: str | None = None,
        model: str | None = None,
    ):
        self.run_command = run_command
        self.timeout = timeout
        self.provider = provider
        self.model = model

    def synthesize(self, topic: str, sources: list[Source]) -> DraftBrief:
        source_packet = "\n\n".join(
            f"[{source.id}] {source.title}\nURL: {source.url}\n"
            f"TYPE: {source.source_type}\nPUBLISHER: {source.publisher}\n"
            f"PUBLISHED: {source.published_at or 'unknown'}\n"
            f"CONTENT SHA256: {source.content_hash}\nTEXT: {source.content}"
            for source in sources
        )
        prompt = f"""You are a careful research analyst. Write a short research brief about:
{topic}

Use ONLY the source packet below. Do not use prior knowledge. Keep every claim narrow and
extractive: reuse the source's substantive terminology rather than adding broad conclusions,
causal language, or unsupported adjectives. Every summary and finding must cite one or more
source IDs exactly like [S1]. For the summary and each finding, attach enough exact quotes
copied verbatim from cited sources to support the entire claim. Use claim_id "summary" for
the summary and "finding_1", "finding_2", etc. for findings. Explicitly identify disagreement,
evidence gaps, source limitations, and uncertainty. Never invent a source, quote, or URL.

SOURCE PACKET
{source_packet}

Return ONLY valid JSON with this exact shape (no markdown fences):
{{"summary":"2-4 sentence synthesis with citations","findings":["3-5 concise cited findings"],"uncertainty":["1-3 cited limitations or open questions"],"evidence":[{{"claim_id":"summary","spans":[{{"source_id":"S1","quote":"exact quote copied from source text"}}]}},{{"claim_id":"finding_1","spans":[{{"source_id":"S1","quote":"exact quote copied from source text"}}]}}]}}
"""
        command = ["hermes", "chat", "-q", prompt, "-Q"]
        if self.provider:
            command.extend(["--provider", self.provider])
        if self.model:
            command.extend(["-m", self.model])
        result = self.run_command(
            command,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"Hermes failed: {error}")
        payload = _extract_json(result.stdout)
        try:
            evidence = [
                ClaimEvidence(
                    claim_id=str(item["claim_id"]).strip(),
                    spans=[
                        EvidenceSpan(
                            source_id=str(span["source_id"]).strip(),
                            quote=str(span["quote"]).strip(),
                        )
                        for span in item.get("spans", [])
                    ],
                )
                for item in payload.get("evidence", [])
            ]
            return DraftBrief(
                summary=str(payload["summary"]).strip(),
                findings=[str(item).strip() for item in payload["findings"]],
                uncertainty=[str(item).strip() for item in payload["uncertainty"]],
                evidence=evidence,
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Hermes returned an invalid brief schema: {exc}") from exc
