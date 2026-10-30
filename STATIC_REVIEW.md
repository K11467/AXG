# Bounded static review — local 7B adaptation

Reviewed current working tree on `local-7b-repro`, 2026-10-30 (Asia/Shanghai). Scope: local inference/input preparation, official-layout bridge, graph request export, both PowerShell orchestration scripts and upstream-script changes. No GPU execution or new data research. No implementation files changed.

## Findings

### [P2] Cleaned action names are stripped again and lose the actual instruction

- `alignment_requests.py:25` passes `action['name']` as a step description to `make_case`.
- `local_inputs.py:43` unconditionally applies `.split('-', 1)[-1]`, expecting the original `Verb-Description` annotation format.
- Upstream alignment names are already cleaned descriptions. The real current action `Fill a microwave-safe mug with skimmed milk` therefore becomes `safe mug with skimmed milk`. The graph reasoning prompt no longer tells the model to fill milk or use a microwave-safe mug, while baseline inference still receives the intact description. Preserve a cleaned action verbatim in this bridge or make prefix stripping explicit for raw annotations only.

### [P2] Unparseable responses become permanently cached successes

- `local_inference.py:89` marks every generated response `status='ok'`; `:100` can then add `parse_ok=False`.
- `local_inference.py:37` skips any matching existing `status='ok'` result, regardless of parse validity.
- `alignment_requests.py:45` refuses unparseable graph results, so one malformed 7B response stops export/evaluation. Restarting exactly the same inference command skips the offending request and fails in the same place. Distinguish successful generation from successful reason parsing, and permit a bounded retry or explicit invalid-result retry. Do not assign a fabricated fallback correctness score.

### [P2] Score exactly 0.5 has opposite classifications in local and official evaluation

- `local_inputs.py:17` sets `is_error = correctness_score <= 0.5`.
- `evaluate_error_detection.py:104` and `:118` instead classify only `error_score > 0.5`; with `error_score=1-correctness_score`, a correctness score of exactly 0.5 is normal there.
- `alignment_requests.py:48` exports both contradictory values unchanged. Thus the JSON prediction and baseline report can call a segment erroneous while the official metric code counts it normal. Pick one documented boundary for the adaptation and use it consistently; if retaining the upstream boundary, disclose the difference from the paper wording.

### [P2] Graph restart consumes stale status from any previous bootstrap run

- `graph_pipeline.ps1:24–26` reads the entire append-only `logs/bootstrap-status.log` and matches any historical ready/failure line.
- `overnight_bootstrap.ps1:15`, `:22`, `:36`, `:39` always append to the same file.
- After one failed bootstrap, relaunching bootstrap and graph concurrently can make graph abort immediately on the old `FAILED:` while the new bootstrap is still running. After a prior successful bootstrap it can instead start immediately on old `BASELINE_AND_CAPTIONS_READY`, before the new run's captions exist. Associate readiness/failure with a current run ID, or explicitly initialize a new run status before orchestration.

## Other reviewed concerns

- No direct leakage of `has_errors`, error descriptions or modified erroneous descriptions into current inference requests was found. GT action names/timestamps are intentionally used and disclosed as GT-segment inference.
- Training/test recording overlap and annotated errors in training recordings are rejected by `prepare_public_data.py`.
- BG drop predictions explicitly identify their source as graph dropping rather than a fabricated VLM score.
- Sparse-caption SentenceBERT projection is substantially different from the paper's visual features, but this is explicitly disclosed by provenance and the report generator.
- This was static review only. It does not establish CUDA compatibility, successful 7B loading, inference completion, or graph-pipeline success.

## Resolution audit (primary agent, 2026-10-30 00:08 CST)

- Finding 1 fixed with a failing-then-passing regression for a cleaned microwave-safe action.
- Finding 2 fixed: only parsed reasoning is a cached success. Invalid output saves status=parse_error and stops the pipeline with an explicit recovery path (--strict-output / --retry-invalid); no invented score or unbounded automatic retry.
- Finding 3 fixed: evaluation now uses error_score>=0.5, matching correctness<=0.5. Boundary regression added; this modification is disclosed.
- Finding 4 fixed: current bootstrap publishes an atomic JSON state with run UUID and PID. Graph worker requires that PID to match bootstrap.pid; historical text logs do not control readiness. Both waiting workers restarted before installation began, and actual state JSON plus live PIDs were verified.
- 13 unittest checks and compile checks pass; actual CUDA/model/graph execution is still pending downloads. This audit does not establish end-to-end success.
