# AI Research Assistant

A small, citation-first agent that turns a research question into a short Markdown brief. It gathers up to five inspectable sources, asks Hermes Agent to synthesize only those sources, checks the citations programmatically, and makes uncertainty explicit.

This is an educational portfolio project, not a fact-checking service. The default collector uses Wikipedia summaries for reproducibility and a small scope; important decisions should be checked against primary sources.

## What the project does

Given a topic, the agent:

1. Searches Wikipedia for a deliberately small source set (1–5 pages).
2. Converts each source into a numbered evidence packet (`S1`, `S2`, ...).
3. Calls the locally installed Hermes Agent CLI for constrained synthesis.
4. Requires citations in the summary and every finding.
5. Rejects citations that do not refer to a collected source.
6. Requires an uncertainty section.
7. Produces a readable Markdown brief and reference list.

The code separates collection, synthesis, evaluation, and rendering so each stage can be tested or replaced independently.

## Why I built it

Research agents often produce fluent answers that hide weak evidence, unsupported claims, or uncertainty. I built this project to explore a narrower question: how much reliability can be added with a small, inspectable workflow around an LLM?

It demonstrates agent workflow design, tool use, prompt constraints, deterministic validation, test-driven development, failure handling, and responsible communication of limitations. Hermes Agent is the reasoning tool in the workflow, but the project is about producing more auditable research briefs rather than showcasing a framework by itself.

## Tools used

- Python 3.11+
- Hermes Agent CLI for synthesis
- Wikipedia MediaWiki and REST APIs for source gathering
- `uv` for environments and commands
- `pytest` for behavioral tests
- `ruff` for linting
- GitHub Actions for continuous integration

No Python runtime dependencies are required; collection uses the standard library.

## How the agent workflow works

```text
Topic
  |
  v
WikipediaCollector ----> small evidence packet with S1...Sn
  |                                  |
  |                                  v
  +--------------------------> HermesSynthesizer
                                      |
                                      v
                                  Draft JSON
                                      |
                                      v
                              deterministic evaluator
                           / unknown source ID? reject
                          / missing claim citation? reject
                         / no uncertainty? reject
                                      |
                                      v
                             cited Markdown brief
```

The model receives the source packet directly and is told to use only that packet. The evaluator does not ask the model whether its own citations are valid; it checks IDs and citation coverage in Python.

### Project structure

```text
src/research_assistant/
  collectors.py   # bounded source retrieval
  hermes.py       # prompt and Hermes CLI adapter
  evaluation.py   # deterministic citation checks
  pipeline.py     # workflow orchestration and rendering
  cli.py          # command-line interface
tests/             # unit and workflow tests
examples/          # brief produced by a real end-to-end run
```

## Setup

Prerequisites:

- Python 3.11 or newer
- `uv`
- Hermes Agent installed and authenticated (`hermes doctor` is useful)

```bash
git clone https://github.com/Saj8292008/ai-research-assistant.git
cd ai-research-assistant
uv sync --extra dev
```

Hermes can use its configured default model, or the CLI can override provider and model explicitly.

## Usage

```bash
uv run research-assistant \
  "How do AI agents use tools?" \
  --max-sources 2 \
  --provider openai-codex \
  --model gpt-5.6-sol \
  --output brief.md
```

If your Hermes default provider works, omit `--provider` and `--model`:

```bash
uv run research-assistant "What are the limitations of retrieval-augmented generation?"
```

## Example input and output

Input:

```text
How do AI agents use tools?
```

Excerpt from a real run:

```markdown
## Summary

AI agents use software or other tools to pursue goals and take actions with some level of autonomy [S2]. The packet distinguishes these agents from "tool AI," which performs narrow, specified tasks, but it does not explain the mechanisms by which agents select, invoke, or coordinate tools [S2].

## Uncertainty

- The packet does not describe how agents choose tools, supply inputs, interpret outputs, handle failures, or decide when to act [S2].
- Both sources are brief Wikipedia excerpts, so the evidence lacks technical detail, primary-source support, empirical results, and information about risks or reliability [S1][S2].
```

See the complete generated brief in [`examples/ai-agents-brief.md`](examples/ai-agents-brief.md).

## Reliability and evaluation

The project uses layered safeguards:

- **Bounded evidence:** at most five sources enter a run.
- **Grounded prompt:** the model is instructed to use only supplied text.
- **Stable source IDs:** citations must use collected IDs such as `[S1]`.
- **Unknown-citation rejection:** `[S9]` fails if no `S9` source exists.
- **Citation coverage:** the summary and every finding need a citation.
- **Required uncertainty:** a brief without limitations/open questions fails.
- **Dependency injection:** fake collectors and synthesizers make edge cases deterministic in tests.
- **Fail closed:** collection, invalid JSON, Hermes failures, and validation failures return an error instead of a plausible-looking brief.

The automated test suite covers valid briefs, invented citations, missing citations, no-source failures, API normalization, Hermes JSON parsing, provider overrides, CLI failures, citation coverage, and uncertainty detection.

Run quality checks:

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
```

## What went wrong during testing

1. **The configured Hermes provider was stale.** The first end-to-end run failed because the local Hermes config still named an unavailable provider. The original adapter only read `stderr`, while Hermes reported the useful error in `stdout`.
   - Improvement: added `--provider` and `--model` overrides and surfaced errors from either stream.

2. **Search relevance was imperfect.** For “How do AI agents use tools?”, one of the two pages was about Claude and contributed little direct evidence.
   - Improvement: the brief explicitly reported the weak source in its uncertainty section rather than stretching it into a stronger claim.

3. **Model output is not automatically trustworthy.** Valid JSON can still contain invented citation IDs or uncited prose.
   - Improvement: added deterministic post-generation checks and tests that prove invalid drafts are rejected.

4. **A small source set improves auditability but limits completeness.** Two short encyclopedia summaries cannot support a deep technical conclusion.
   - Improvement: cap claims to the supplied evidence and expose the limitation in every brief.

## Responsible AI choices

- The application labels uncertainty rather than presenting synthesis as settled fact.
- It links every collected source so a reader can inspect the evidence.
- It does not hide failures behind fallback prose.
- It avoids autonomous publishing or decision-making.
- It clearly states that Wikipedia summaries are not a substitute for primary research.

Citation validation proves that a cited ID exists; it does **not** prove that the sentence accurately represents the source. That remaining entailment problem is the largest reliability limitation in this MVP.

## What I would build next

1. Add primary-source collectors for arXiv, Crossref, and government domains.
2. Rank sources for relevance, authority, recency, and diversity.
3. Fetch full text and attach sentence-level evidence spans to each claim.
4. Add an independent entailment checker rather than only validating citation IDs.
5. Detect conflicts between sources and represent competing conclusions.
6. Create a benchmark dataset with expected citations and human quality ratings.
7. Add caching, retry/backoff, rate-limit handling, and provenance metadata.
8. Build a small web UI that lets users inspect each claim beside its evidence.

## License

MIT
