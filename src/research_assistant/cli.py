from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .collectors import (
    ArxivCollector,
    CrossrefCollector,
    DataGovCollector,
    MultiSourceCollector,
    WikipediaCollector,
)
from .hermes import HermesSynthesizer
from .http_client import CachedHttpClient
from .pipeline import ResearchPipeline

COLLECTORS = {
    "arxiv": ArxivCollector,
    "crossref": CrossrefCollector,
    "government": DataGovCollector,
    "wikipedia": WikipediaCollector,
}


def build_collector(source_types: list[str], cache_dir: Path) -> MultiSourceCollector:
    client = CachedHttpClient(cache_dir)
    return MultiSourceCollector([COLLECTORS[name](http_get=client.get) for name in source_types])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a claim-evidence research brief with Hermes Agent."
    )
    parser.add_argument("topic", help="Topic or research question")
    parser.add_argument("--max-sources", type=int, default=5, choices=range(1, 11))
    parser.add_argument("--output", type=Path, help="Write Markdown to this path")
    parser.add_argument("--html-output", type=Path, help="Write the evidence inspector UI")
    parser.add_argument(
        "--source",
        action="append",
        choices=tuple(COLLECTORS),
        dest="sources",
        help="Source family to use; repeat the option to select several (default: all)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("~/.cache/ai-research-assistant").expanduser(),
    )
    parser.add_argument("--provider", help="Hermes provider override, e.g. openai-codex")
    parser.add_argument("--model", help="Hermes model override, e.g. gpt-5.6-sol")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source_types = args.sources or list(COLLECTORS)
    try:
        result = ResearchPipeline(
            build_collector(source_types, args.cache_dir),
            HermesSynthesizer(provider=args.provider, model=args.model),
        ).run(args.topic, args.max_sources)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"Research failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result.markdown, encoding="utf-8")
        print(f"Wrote {result.source_count}-source brief to {args.output}")
    else:
        print(result.markdown)

    if args.html_output:
        args.html_output.parent.mkdir(parents=True, exist_ok=True)
        args.html_output.write_text(result.html, encoding="utf-8")
        print(f"Wrote evidence inspector to {args.html_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
