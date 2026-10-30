$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$repoRoot = 'C:\Dev\AXG-Reasoner'
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'
Set-Location -LiteralPath $repoRoot
$env:AXG_SENTENCE_MODEL = 'C:/Dev/axg-cache/all-MiniLM-L6-v2'
$env:MPLBACKEND = 'Agg'
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$runId = [guid]::NewGuid().ToString()

function Invoke-GraphStep([string]$StepName, [string[]]$Arguments) {
    "$(Get-Date -Format o) START $StepName" | Add-Content 'logs\graph-status.log'
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $pythonExe @Arguments *> "logs\$StepName.log"
    $nativeExit = $LASTEXITCODE
    $ErrorActionPreference = $savedPreference
    if ($nativeExit -ne 0) { throw "$StepName exited $nativeExit; inspect logs/$StepName.log" }
    "$(Get-Date -Format o) COMPLETE $StepName" | Add-Content 'logs\graph-status.log'
}

try {
    $deadline = (Get-Date).AddHours(10)
    while ($true) {
        if ((Get-Date) -gt $deadline) { throw 'Timed out waiting for generated captions' }
        $stateText = Get-Content -LiteralPath 'logs\bootstrap-state.json' -Raw -ErrorAction SilentlyContinue
        $expectedPid = Get-Content -LiteralPath 'logs\bootstrap.pid' -ErrorAction SilentlyContinue
        if ($stateText) {
            $state = $stateText | ConvertFrom-Json
            if ([string]$state.pid -eq [string]$expectedPid) {
                if ($state.status -eq 'ready') { break }
                if ($state.status -eq 'failed') { throw "Current bootstrap failed: $($state.step)" }
            }
        }
        Start-Sleep -Seconds 30
    }
    while (-not (Test-Path -LiteralPath 'C:\Dev\axg-cache\all-MiniLM-L6-v2\download_provenance.json')) {
        if ((Get-Date) -gt $deadline) { throw 'Timed out waiting for sentence model' }
        Start-Sleep -Seconds 30
    }
    Invoke-GraphStep 'prepare-official-layout' @('-u','prepare_official_layout.py')
    Invoke-GraphStep 'official-clustering' @('-u','generate_subactions_objects.py','--dataset','CaptainCook4D','--task','spicedhotchocolate')
    Invoke-GraphStep 'official-summaries' @('-u','summarize_subactions.py','--dataset','CaptainCook4D','--task','spicedhotchocolate','--model-name','C:/Dev/axg-cache/Qwen2.5-VL-7B-Instruct','--vision-language-model')
    @{summary_model='Qwen/Qwen2.5-VL-7B-Instruct'; summary_revision='cc594898137f460bfe9f0759e9844b3ce807cfb5';
      summary_backend='Qwen2_5_VLForConditionalGeneration-text-only'; vision_model='Qwen/Qwen2.5-VL-7B-Instruct';
      run_id=$runId; status_log='logs/graph-status.log'; updated=(Get-Date -Format o)} |
      ConvertTo-Json | Set-Content 'output/local7b/run_provenance.json' -Encoding UTF8
    Invoke-GraphStep 'official-subaction-features' @('-u','generate_subaction_features.py','--dataset','CaptainCook4D','--task','spicedhotchocolate')
    Invoke-GraphStep 'official-build-axg' @('-u','build_axg.py','--dataset','CaptainCook4D','--task','spicedhotchocolate','--min-path-count','1')
    Invoke-GraphStep 'official-alignment' @('-u','axg2vid.py','--dataset','CaptainCook4D','--task','spicedhotchocolate','--tas_backbone','gt','--min-action-captions','1','--min-bg-captions','2')
    Invoke-GraphStep 'prepare-graph-inference' @('alignment_requests.py','prepare')
    Invoke-GraphStep 'axg-inference' @('-u','local_inference.py','--manifest','output\local7b\axg_requests.json','--output','output\local7b\axg_results')
    Invoke-GraphStep 'export-graph-results' @('alignment_requests.py','export')
    Invoke-GraphStep 'official-error-detection' @('-u','evaluate_error_detection.py','--dataset','CaptainCook4D','--task','spicedhotchocolate','--tas_backbone','gt')
    Invoke-GraphStep 'prepare-comparison' @('prepare_comparison_inputs.py')
    Invoke-GraphStep 'baseline-8f' @('-u','local_inference.py','--manifest','output/local7b/baseline_requests_8f.json','--output','output/local7b/baseline_results_8f')
    Invoke-GraphStep 'graph-8f' @('-u','local_inference.py','--manifest','output/local7b/axg_requests_8f.json','--output','output/local7b/axg_results_8f')
    Invoke-GraphStep 'audit-comparison' @('audit_experiment.py')
    Invoke-GraphStep 'generate-report' @('generate_report.py')
    "$(Get-Date -Format o) GRAPH_PIPELINE_FINISHED; human/agent must audit actual results" | Add-Content 'logs\graph-status.log'
}
catch {
    "$(Get-Date -Format o) FAILED: $_" | Add-Content 'logs\graph-status.log'
    exit 1
}
