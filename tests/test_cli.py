from research_assistant.cli import build_collector, build_parser
from research_assistant.collectors import ArxivCollector, DataGovCollector


def test_cli_builds_selected_cached_primary_source_collectors(tmp_path):
    collector = build_collector(["arxiv", "government"], tmp_path)

    assert [type(item) for item in collector.collectors] == [ArxivCollector, DataGovCollector]
    assert collector.collectors[0].http_get.__self__.cache_dir == tmp_path


def test_cli_accepts_html_output_and_ten_sources():
    args = build_parser().parse_args(
        ["AI agents", "--max-sources", "10", "--html-output", "brief.html"]
    )

    assert args.max_sources == 10
    assert str(args.html_output) == "brief.html"
