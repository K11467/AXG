# Final bounded static review

Reviewed current files on 2026-10-30 (Asia/Shanghai). No GPU execution, downloads, new agents, or implementation edits. Read the actual current inference, EgoVLP extraction/layout, graph export, report aggregation, and background PowerShell entry points.

## One remaining important finding

### [P2] Graph export and caption-layout conversion can select results from a different request with the same ID

- `alignment_requests.py:49–55` reads all graph result JSON files and selects the latest by `id`, without checking `status`, stored `request`, or the request signature against the active manifest.
- `prepare_official_layout.py:31–35` similarly accepts the latest successful caption result by `id`, without comparing the saved request to the current caption request.
- IDs remain stable when captions, subaction text, timing, prompt or graph changes. In particular graph IDs are only recording/action-index/subaction-index. A retry with changed requests can therefore consume an old successful response even when the current request has no valid result; conversely a newer invalid response from an unrelated request can hide an older valid matching result. The report loader now compares the request, so official exported metrics and the report can disagree about which results exist.
- Require a matching stored request (allowing the documented strict-output formatting variant where intended) and valid successful status before accepting results. The existing request comparison in `generate_report.py:18–24` is a useful pattern. Keep runtime configuration/signature provenance with exported results if multiple inference settings are retained.

This is a restart/provenance issue; there are currently no 7B prediction files, so it has not yet contaminated results.

## Reviewed without a new blocking finding

- Previous action-hyphen truncation, permanently cached parse failures, 0.5 threshold inconsistency, and whole-history bootstrap status matching have been corrected in current files.
- `extract_egovlp_features.py` uses strict video/projection loading, safe metadata substitution, finite/shape checks, and records checkpoint/source provenance. The supplied actual extraction log records 443+422+263 = 1128 finite 256D features. Static review does not independently verify GPU execution.
- No direct error-label/description leakage into the current model requests or visual features was found. GT action labels/times are the disclosed conditioning; error flags stay in evaluation labels.
- Current background entry uses caption stride 1, real EgoVLP layout by default, and documented sparse-data graph thresholds. Current preparation default is also stride 1.
- `result_summary.py` keeps incomplete predictions unknown and withholds complete metrics; graph drop scores identify their algorithmic source.
- No new deterministic Windows incompatibility or immediate inference-stopping code defect was identified by this bounded review. Actual 7B generation remains unverified until the weight download and model run finish.

## Resolution 2026-10-30 01:49 CST
The remaining P2 finding is fixed. Caption layout, graph export, and reporting now share `result_summary.load_matching_results`, requiring successful status and identical saved request inputs (allowing the documented strict-output variant). A regression test for changed prompts with stable caption/reason IDs failed before implementation and passes afterward. Full suite: 22 tests pass. No 7B outputs existed during this fix.

## Final handoff review and replay verification (2026-10-30)
A fresh-context bounded read-only reviewer found no Critical issue in the completed experiment, but identified that replaying the VL-text pipeline after the independent-text run could mix provenance and 8-frame outputs. Owner inspection also found surplus numerical prototype files when rebuilding a smaller graph.

Both are fixed: each pipeline writes its actual summary-model provenance, rebuilds both frame configurations and audits them; prototype generation removes only surplus numbered outputs and refuses unknown files/empty summaries. Two regression tests were observed failing before implementation, then the full suite passed 25 tests. The reviewer inspected the correction and found no new consequential issue, contingent on actual replay/restoration.

That condition is now verified: session81639 ran the corrected VL-text pipeline to exit0, with matching 3/8-frame graph inputs (7 requests each), correct VL-text provenance, 14 prototype arrays and successful audit. The independently learned text-7B round was then restored from its 128-file immutable snapshot; all restored official files match the snapshot, the current audit has 12 learned subactions/24 prototype arrays and 10 graph requests per frame setting. Both historical snapshots remain unchanged. See logs/replay-consistency-audit.json, logs/final-restored-audit.log and logs/final-data-audit.json.

Declined judgments: exact paper equivalence, scientific generalization and quantitative explanation quality; author preprocessing is unavailable, the test sample is one recording/five observed actions, and no explanation benchmark is computed. These are explicit scope limits, not claimed outcomes. No merge or remote push was requested. Local handoff is ready.
