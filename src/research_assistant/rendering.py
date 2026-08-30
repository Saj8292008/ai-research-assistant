from __future__ import annotations

import html
from collections import defaultdict
from urllib.parse import urlparse

from .models import DraftBrief, Source


def _safe_link(url: str) -> str:
    return url if urlparse(url).scheme in {"http", "https"} else "#"


def render_inspection_html(topic: str, draft: DraftBrief, sources: list[Source]) -> str:
    source_map = {source.id: source for source in sources}
    evidence = defaultdict(list)
    for item in draft.evidence:
        evidence[item.claim_id].extend(item.spans)

    claims = [("summary", "Summary", draft.summary)] + [
        (f"finding_{index}", f"Finding {index}", text)
        for index, text in enumerate(draft.findings, 1)
    ]
    cards = []
    for claim_id, label, text in claims:
        spans = []
        for span in evidence.get(claim_id, []):
            source = source_map.get(span.source_id)
            if not source:
                continue
            spans.append(
                f'<div class="evidence"><blockquote>{html.escape(span.quote)}</blockquote>'
                f'<a href="{html.escape(_safe_link(source.url), quote=True)}">[{html.escape(source.id)}] '
                f"{html.escape(source.title)}</a><small>"
                f"{html.escape(source.publisher or source.source_type)} · type "
                f"{html.escape(source.source_type)} · published "
                f"{html.escape(source.published_at or 'unknown')} · cache "
                f"{'hit' if source.from_cache else 'miss'} · rank "
                f"{source.relevance_score:.4f} · sha256 "
                f"{html.escape(source.content_hash)} · fetched "
                f"{html.escape(source.fetched_at)}</small></div>"
            )
        cards.append(
            f'<article><section><span class="label">{label}</span><p>{html.escape(text)}</p></section>'
            f"<aside>{''.join(spans) or '<em>No verified evidence attached</em>'}</aside></article>"
        )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Evidence Inspector — {html.escape(topic)}</title>
<style>
:root{{--bg:#0b1020;--panel:#121a2f;--text:#eef2ff;--muted:#9aa7c7;--accent:#73e0c1}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:16px system-ui}}
main{{max-width:1100px;margin:auto;padding:40px 20px}} h1{{margin-bottom:6px}} .sub{{color:var(--muted)}}
article{{display:grid;grid-template-columns:1fr 1fr;gap:20px;background:var(--panel);padding:20px;margin:18px 0;border-radius:14px}}
.label{{color:var(--accent);font-weight:700}} blockquote{{margin:0 0 10px;border-left:3px solid var(--accent);padding-left:12px}}
a{{color:var(--accent)}} small{{display:block;color:var(--muted);margin-top:4px}} em{{color:#ffb4a9}}
@media(max-width:720px){{article{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>Evidence Inspector</h1><p class="sub">{html.escape(topic)}</p>
{"".join(cards)}</main></body></html>"""
