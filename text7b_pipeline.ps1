$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
Set-Location -LiteralPath 'C:\Dev\AXG-Reasoner'
$pythonExe = 'C:\Dev\AXG-Reasoner\.venv\Scripts\python.exe'
$env:AXG_SENTENCE_MODEL = 'C:/Dev/axg-cache/all-MiniLM-L6-v2'
$env:MPLBACKEND = 'Agg'
$runId = [guid]::NewGuid().ToString()
$PID | Set-Content -LiteralPath 'logs/text7b-pipeline.pid'

function Set-RunState([string]$Phase, [string]$Step) {
    @{run_id=$runId; status=$Phase; step=$Step; pid=$PID; updated=(Get-Date -Format o)} |
        ConvertTo-Json | Set-Content -LiteralPath 'logs/text7b-state.tmp' -Encoding UTF8
    Move-Item -LiteralPath 'logs/text7b-state.tmp' -Destination 'logs/text7b-state.json' -Force
}
function Invoke-Stage([string]$Name, [string[]]$Arguments) {
    Set-RunState 'running' $Name
    "$(Get-Date -Format o) START $Name" | Add-Content 'logs/text7b-status.log'
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $pythonExe @Arguments *> "logs/text7b-$Name.log"
    $nativeExit = $LASTEXITCODE
    $ErrorActionPreference = $savedPreference
    if ($nativeExit -ne 0) { throw "$Name exited $nativeExit; inspect logs/text7b-$Name.log" }
    "$(Get-Date -Format o) COMPLETE $Name" | Add-Content 'logs/text7b-status.log'
}
try {
    Set-RunState 'waiting' 'verified-text-model'
    $deadline = (Get-Date).AddHours(5)
    while (-not (Test-Path -LiteralPath 'C:/Dev/axg-cache/Qwen2.5-7B-Instruct/download_provenance.json')) {
        if ((Get-Date) -gt $deadline) { throw 'Timed out waiting for verified text 7B weights' }
        Start-Sleep -Seconds 30
    }
    $baseState = Get-Content 'logs/bootstrap-state.json' -Raw | ConvertFrom-Json
    if ($baseState.status -ne 'ready') { throw 'Caption/bootstrap is not ready; refusing overlapping or incomplete run' }
    Invoke-Stage 'prepare-layout' @('-u','prepare_official_layout.py')
    Invoke-Stage 'clustering' @('-u','generate_subactions_objects.py','--dataset','CaptainCook4D','--task','spicedhotchocolate')
    Invoke-Stage 'summaries' @('-u','summarize_subactions.py','--dataset','CaptainCook4D','--task','spicedhotchocolate','--model-name','C:/Dev/axg-cache/Qwen2.5-7B-Instruct')
    @{summary_model='Qwen/Qwen2.5-7B-Instruct'; summary_revision='a09a35458c702b33eeacc393d103063234e8bc28';
      summary_backend='AutoModelForCausalLM'; vision_model='Qwen/Qwen2.5-VL-7B-Instruct';
      run_id=$runId; status_log='logs/text7b-status.log'; updated=(Get-Date -Format o)} |
      ConvertTo-Json | Set-Content 'output/local7b/run_provenance.json' -Encoding UTF8
    Invoke-Stage 'subaction-features' @('-u','generate_subaction_features.py','--dataset','CaptainCook4D','--task','spicedhotchocolate')
    Invoke-Stage 'build-axg' @('-u','build_axg.py','--dataset','CaptainCook4D','--task','spicedhotchocolate','--min-path-count','1')
    Invoke-Stage 'alignment' @('-u','axg2vid.py','--dataset','CaptainCook4D','--task','spicedhotchocolate','--tas_backbone','gt','--min-action-captions','1','--min-bg-captions','2')
    Invoke-Stage 'prepare-requests' @('alignment_requests.py','prepare')
    Invoke-Stage 'inference-3f' @('-u','local_inference.py','--manifest','output/local7b/axg_requests.json','--output','output/local7b/axg_results')
    Invoke-Stage 'export-3f' @('alignment_requests.py','export')
    Invoke-Stage 'evaluate-3f' @('-u','evaluate_error_detection.py','--dataset','CaptainCook4D','--task','spicedhotchocolate','--tas_backbone','gt')
    Invoke-Stage 'prepare-8f' @('prepare_comparison_inputs.py')
    Invoke-Stage 'baseline-8f' @('-u','local_inference.py','--manifest','output/local7b/baseline_requests_8f.json','--output','output/local7b/baseline_results_8f')
    Invoke-Stage 'graph-8f' @('-u','local_inference.py','--manifest','output/local7b/axg_requests_8f.json','--output','output/local7b/axg_results_8f')
    Invoke-Stage 'audit' @('audit_experiment.py')
    Invoke-Stage 'report' @('generate_report.py')
    Set-RunState 'finished' 'TEXT7B_PIPELINE_FINISHED_REQUIRES_AGENT_AUDIT'
    "$(Get-Date -Format o) TEXT7B_PIPELINE_FINISHED; agent must inspect real outputs" | Add-Content 'logs/text7b-status.log'
}
catch {
    Set-RunState 'failed' ([string]$_)
    "$(Get-Date -Format o) FAILED: $_" | Add-Content 'logs/text7b-status.log'
    exit 1
}
