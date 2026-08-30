# Research Brief: How do AI agents use external tools reliably?

## Summary

The directly relevant study describes agent tool use through “versioned repository-level artifacts” and eight configuration mechanisms spanning static context, executable mechanisms, and external integrations [S1]. It reports that Context Files dominate current adoption, while experimental evidence about how configuration strategies affect agent performance remains an open research need [S1].

## Key Findings

- Developers can configure agentic AI coding tools through versioned repository-level Markdown and JSON artifacts [S1].
- The study identifies eight configuration mechanisms, ranging from static context to executable and external integrations [S1].
- Context Files are often the sole configuration mechanism in a repository, and AGENTS.md is emerging as an interoperable standard across tools [S1].
- Advanced mechanisms such as Skills and Subagents have limited adoption, and Skills predominantly contain static instructions rather than executable scripts [S1].

## Evidence

- **summary — [S1]**: “Developers can configure these tools through versioned repository-level artifacts such as Markdown and JSON files.”
- **summary — [S1]**: “We identify eight configuration mechanisms spanning from static context to executable and external integrations”
- **summary — [S1]**: “First, Context Files dominate the configuration landscape and are often the sole mechanism in a repository, with AGENTS$.$md emerging as an interoperable standard across tools.”
- **summary — [S1]**: “These findings establish an empirical baseline for understanding how developers configure agentic tools, suggest that AGENTS$.$md serves as a natural starting point, and motivate longitudinal and experimental research on how configuration strategies evolve and affect agent performance.”
- **finding_1 — [S1]**: “Developers can configure these tools through versioned repository-level artifacts such as Markdown and JSON files.”
- **finding_2 — [S1]**: “We identify eight configuration mechanisms spanning from static context to executable and external integrations”
- **finding_3 — [S1]**: “First, Context Files dominate the configuration landscape and are often the sole mechanism in a repository, with AGENTS$.$md emerging as an interoperable standard across tools.”
- **finding_4 — [S1]**: “Second, few repositories adopt advanced mechanisms such as Skills and Subagents. Skills predominantly rely on static instructions rather than executable scripts.”

## Uncertainty

- S1 provides an empirical baseline from 2,853 GitHub repositories but calls for longitudinal and experimental research on how configuration strategies evolve and affect agent performance; it therefore does not establish which mechanisms make external-tool use reliable [S1].
- No disagreement about reliable external-tool use can be identified within the packet: S2 examines students’ intended AI-tool use in study scenarios [S2], while S3 examines how AI predictions shape human decision-making [S3], so neither supplies directly comparable evidence.

## Sources and Provenance

[S1]: https://arxiv.org/abs/2602.14690v5 "Harness Engineering for Agentic AI Coding Tools: An Exploratory Study" — arXiv; published 2026-02-16; remote fetched 2026-08-30T18:15:19.599451+00:00; cache hit; run observed 2026-08-30T18:23:37.447933+00:00; sha256 `788f933619e1f2b9ea1dd07db74881b313b7f6d6221f8015ccefaf61d545b8ba`; rank 0.8833
[S2]: https://doi.org/10.4995/head25.2025.20179 "What do students use AI tools for? Assessing students’ use of AI tools in three typical study related scenarios" — Editorial Universitat Politècnica de València (edUPV); published 2025-06-17; remote fetched 2026-08-30T18:15:19.970076+00:00; cache hit; run observed 2026-08-30T18:23:37.448674+00:00; sha256 `beb721f81b44e70a2842dd3ff3d1b6097b814571d0d9e3a21f8cf59347230a3e`; rank 0.8050
[S3]: https://arxiv.org/abs/2603.28944v2 "Faith in AI can narrow the futures individuals consider" — arXiv; published 2026-03-30; remote fetched 2026-08-30T18:15:19.599451+00:00; cache hit; run observed 2026-08-30T18:23:37.447505+00:00; sha256 `29bcade22832f33cfba0480d5b93d97bc628e0196b12e3782b0ca34ffcd542a5`; rank 0.6667
