import argparse
import sys
from pathlib import Path

from .collectors import WikipediaCollector
from .hermes import HermesSynthesizer
from .pipeline import ResearchPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a short, citation-checked research brief with Hermes Agent."
    )
    parser.add_argument("topic", help="Topic or research question")
    parser.add_argument("--max-sources", type=int, default=3, choices=range(1, 6))
    parser.add_argument("--output", type=Path, help="Write Markdown to this path")
    parser.add_argument("--provider", help="Hermes provider override, e.g. openai-codex")
    parser.add_argument("--model", help="Hermes model override, e.g. gpt-5.6-sol")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = ResearchPipeline(
            WikipediaCollector(),
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
