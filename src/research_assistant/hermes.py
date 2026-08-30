import json
import re
import subprocess
from collections.abc import Callable

from .models import DraftBrief, Source


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
            f"[{source.id}] {source.title}\nURL: {source.url}\nTEXT: {source.content}"
            for source in sources
        )
        prompt = f"""You are a careful research analyst. Write a short research brief about:
{topic}

Use ONLY the source packet below. Do not use prior knowledge. Every summary and finding
must cite one or more source IDs exactly like [S1]. Explicitly identify disagreement,
evidence gaps, source limitations, and uncertainty. Never invent a source or URL.

SOURCE PACKET
{source_packet}

Return ONLY valid JSON with this exact shape (no markdown fences):
{{"summary":"2-4 sentence synthesis with citations","findings":["3-5 concise cited findings"],"uncertainty":["1-3 cited limitations or open questions"]}}
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
            return DraftBrief(
                summary=str(payload["summary"]).strip(),
                findings=[str(item).strip() for item in payload["findings"]],
                uncertainty=[str(item).strip() for item in payload["uncertainty"]],
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Hermes returned an invalid brief schema: {exc}") from exc
