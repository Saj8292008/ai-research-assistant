import json

import pytest

from research_assistant.hermes import HermesSynthesizer
from research_assistant.models import Source


def test_hermes_synthesizer_parses_json_response():
    captured: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        captured.append(command)
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps(
                    {
                        "summary": "A finding [S1].",
                        "findings": ["One result [S1]."],
                        "uncertainty": ["Single source [S1]."],
                        "evidence": [
                            {
                                "claim_id": "summary",
                                "spans": [{"source_id": "S1", "quote": "Some evidence"}],
                            }
                        ],
                    }
                ),
                "stderr": "",
            },
        )()

    draft = HermesSynthesizer(run_command=fake_run).synthesize(
        "AI agents", [Source("S1", "Source", "https://example.com", "Some evidence")]
    )

    assert draft.summary == "A finding [S1]."
    assert draft.evidence[0].spans[0].quote == "Some evidence"
    assert "exact quote" in captured[0][3]
    assert captured[0][:3] == ["hermes", "chat", "-q"]
    assert "Return ONLY valid JSON" in captured[0][3]


def test_hermes_synthesizer_passes_explicit_provider_and_model():
    captured: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        captured.append(command)
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": '{"summary":"A [S1].","findings":["B [S1]."],"uncertainty":["C [S1]."]}',
                "stderr": "",
            },
        )()

    HermesSynthesizer(
        run_command=fake_run, provider="openai-codex", model="gpt-5.6-sol"
    ).synthesize("topic", [Source("S1", "T", "https://example.com", "C")])

    assert "--provider" in captured[0]
    assert "openai-codex" in captured[0]
    assert "-m" in captured[0]
    assert "gpt-5.6-sol" in captured[0]


def test_hermes_synthesizer_reports_cli_failure_from_stdout():
    def fake_run(command: list[str], **kwargs):
        return type("Result", (), {"returncode": 1, "stdout": "bad provider", "stderr": ""})()

    with pytest.raises(RuntimeError, match="bad provider"):
        HermesSynthesizer(run_command=fake_run).synthesize(
            "topic", [Source("S1", "T", "https://example.com", "C")]
        )
