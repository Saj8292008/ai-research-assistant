# AI Research Assistant

A primary-source, claim-evidence research agent powered by Hermes Agent. It collects a bounded source set, ranks evidence, produces a cited brief, attaches exact source passages to every claim, independently checks citation/evidence integrity, and generates an interactive evidence inspector.

This is an educational reliability project—not a fact-checking service. Its deterministic lexical entailment screen catches unsupported or unrelated evidence, but it is not equivalent to expert semantic verification.

## What it does

Given a research question, the agent:

1. Searches configured source families: arXiv, Crossref, Data.gov, and Wikipedia.
2. Normalizes provenance: publisher, authors, publication/retrieval dates, canonical URL, source family, and SHA-256 content hash.
3. Caches API responses and retries transient network failures with exponential backoff.
4. Ranks candidates by topic relevance, source authority, recency, and source-family diversity.
5. Sends a bounded evidence packet to Hermes Agent.
6. Requires citations and exact source quotes for the summary and every finding.
7. Rejects unknown citations, fabricated quotes, missing evidence, and unsupported claims.
8. Produces a Markdown brief plus a responsive HTML evidence inspector.

## Why it exists

Research agents can produce fluent prose while hiding weak retrieval, invented citations, or unsupported claims. This project keeps collection, model synthesis, deterministic evaluation, and presentation as separate stages so failures remain visible and each layer can be tested independently.

Hermes Agent is the reasoning adapter, but the project is about auditable research—not framework demonstration.

## Architecture

```text
research question
      |
      v
arXiv | Crossref | Data.gov | Wikipedia
      |
      v
cached/retried HTTP + normalized provenance
      |
      v
relevance + authority + recency + diversity ranking
      |
      v
bounded evidence packet (S1...Sn)
      |
      v
Hermes constrained synthesis
      |
      v
claims + citations + exact evidence spans
      |
      v
deterministic evaluator
  - known source IDs?
  - exact quote exists in source?
  - every claim has evidence?
  - independent lexical support?
  - uncertainty present?
      |
      +--> Markdown brief
      +--> HTML Evidence Inspector
```

## Source families

- `arxiv`: version-preserving paper URLs, titles, abstracts, authors, and publication dates.
- `crossref`: DOI records with abstracts, authors, publishers, and publication dates.
- `government`: official dataset descriptions from the Data.gov catalog.
- `wikipedia`: reproducible fallback summaries; lower authority weight than primary-source families.

The default run queries all four. Use repeated `--source` flags to restrict collection.

## Setup

Requirements:

- Python 3.11+
- `uv`
- Hermes Agent installed and authenticated

```bash
git clone https://github.com/Saj8292008/ai-research-assistant.git
cd ai-research-assistant
uv sync --extra dev
hermes doctor
```

No runtime Python dependencies are required; the implementation uses the standard library.

## Usage

Primary-source run with both outputs:

```bash
uv run research-assistant \
  "How do AI agents use external tools reliably?" \
  --max-sources 5 \
  --source arxiv \
  --source crossref \
  --source government \
  --provider openai-codex \
  --model gpt-5.6-sol \
  --output brief.md \
  --html-output evidence-inspector.html
```

Use every collector and the configured Hermes default:

```bash
uv run research-assistant \
  "What are the limitations of retrieval-augmented generation?" \
  --output brief.md \
  --html-output brief.html
```

Options:

- `--max-sources 1..10`: bounded final packet size; default 5.
- `--source arxiv|crossref|government|wikipedia`: repeat to select source families.
- `--cache-dir PATH`: cached API responses; default `~/.cache/ai-research-assistant`.
- `--provider` / `--model`: explicit Hermes overrides.
- `--output`: Markdown artifact.
- `--html-output`: self-contained evidence inspector.

## Evidence contract

Hermes returns structured JSON containing:

- `summary`
- `findings`
- `uncertainty`
- `evidence`
  - claim ID (`summary`, `finding_1`, ...)
  - cited source ID
  - exact quote copied from source text

The evaluator checks this outside the model. Every summary/finding must:

- contain a known citation,
- have at least one evidence span,
- quote text that occurs exactly in the cited source,
- pass an independent lexical support screen.

Evidence from multiple quotes is combined for multi-part claims. Lightweight stemming handles basic paraphrases. A claim passes when overlap is strong or when at least two substantive claim terms appear with sufficient coverage. A conservative polarity check rejects claim/evidence pairs when only one side contains explicit negation; this catches simple contradictions but is not a general natural-language inference model.

## Evidence Inspector

The generated HTML page displays each claim beside:

- its exact evidence passage,
- source ID and title,
- publisher/source family,
- direct source link,
- publication/fetch dates, cache status, ranking score, and content hash.

It is self-contained and needs no server. The checked-in real example is:

- `examples/primary-sources-brief.md`
- `examples/primary-sources-inspector.html`

## Reliability behavior

The pipeline fails closed when:

- every collector fails or produces no usable source,
- Hermes fails or returns invalid JSON/schema,
- a citation ID was not collected,
- a summary or finding lacks a citation,
- an evidence quote is absent from its source,
- an evidence source is not cited by its claim,
- a claim lacks exact evidence,
- the independent entailment screen finds insufficient support,
- uncertainty is missing.

It never replaces a rejected run with plausible fallback prose.

## Testing

```bash
uv run pytest -q
uv run ruff check .
uv build
```

The suite covers:

- all four source normalizers,
- source ranking and diversity,
- cache hits and bounded retries,
- provenance and content hashes,
- Hermes structured-evidence parsing,
- provider/model overrides,
- citation validity and coverage,
- exact-quote validation,
- aggregate multi-span support,
- supported paraphrases,
- explicit-negation contradictions,
- symbol-heavy ranking queries,
- fail-closed pipeline behavior,
- HTML escaping, safe links, provenance, and claim/evidence presentation,
- CLI source selection and output options.

GitHub Actions runs tests and linting on every push.

## Real executed example

The repository includes a real network + Hermes run for:

```text
How do AI agents use external tools reliably?
```

The run collected and ranked three sources, generated claim-level evidence, passed citation/evidence/entailment checks, and produced both example artifacts. The brief explicitly reports that only one source directly addressed agent configuration; the others were weaker contextual evidence. This is expected behavior: weak retrieval must be exposed, not stretched into certainty.

## What went wrong and what improved

1. The original MVP relied only on Wikipedia summaries.
   - Added arXiv, Crossref, and Data.gov collectors while retaining Wikipedia as a fallback.

2. Search APIs returned tangential results.
   - Added relevance, authority, recency, and source-diversity ranking; the final brief still discloses weak sources.

3. Citation-ID validation did not prove evidentiary support.
   - Added exact claim-level evidence spans and source-text verification.

4. A strict single-quote lexical threshold rejected valid multi-part summaries.
   - Added aggregate support across all exact quotes attached to a claim and lightweight stemming for paraphrases.

5. Network calls were brittle and repeated unnecessarily.
   - Added bounded retries, exponential backoff, and deterministic disk caching.

6. Markdown made claim/evidence auditing cumbersome.
   - Added a responsive side-by-side HTML evidence inspector.

## Honest limitations

- API search relevance remains imperfect, especially for broad or ambiguous questions.
- Crossref records without abstracts are rejected, reducing coverage.
- Data.gov is useful for official datasets but is not a universal government-document search engine.
- Abstracts and dataset descriptions are not full-text evidence.
- The lexical entailment screen is independent and deterministic, but it is a heuristic—not proof of semantic entailment.
- Source authority is represented by transparent family-level weights, not a universal truth score.
- Human review is still required for consequential research.

## Next steps

- Add full-text extraction with passage offsets.
- Add domain-specific government collectors and Crossref/DOI full-text resolution.
- Add a benchmark set with expected claims, passages, and human entailment labels.
- Compare lexical screening against an independently configured NLI model.
- Add deduplication by DOI/title/content hash and richer conflict detection.
- Add exportable machine-readable run manifests.

## License

MIT
