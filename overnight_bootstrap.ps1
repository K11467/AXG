$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$repoRoot = 'C:\Dev\AXG-Reasoner'
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'
Set-Location -LiteralPath $repoRoot
$runId = [guid]::NewGuid().ToString()

function Set-BootstrapState([string]$Phase, [string]$Step) {
    $state = @{ run_id=$runId; status=$Phase; step=$Step; pid=$PID; updated=(Get-Date -Format o) }
    $state | ConvertTo-Json | Set-Content -LiteralPath 'logs\bootstrap-state.tmp' -Encoding UTF8
    Move-Item -LiteralPath 'logs\bootstrap-state.tmp' -Destination 'logs\bootstrap-state.json' -Force
}

function Wait-Artifact([string]$ArtifactPath) {
    $deadline = (Get-Date).AddHours(9)
    while (-not (Test-Path -LiteralPath $ArtifactPath)) {
        if ((Get-Date) -gt $deadline) { throw "Timed out waiting for $ArtifactPath" }
        Start-Sleep -Seconds 30
    }
}

function Invoke-PythonStep([string]$StepName, [string[]]$Arguments) {
    Set-BootstrapState 'running' $StepName
    "$(Get-Date -Format o) START $StepName" | Add-Content 'logs\bootstrap-status.log'
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $pythonExe @Arguments *> "logs\$StepName.log"
    $nativeExit = $LASTEXITCODE
    $ErrorActionPreference = $savedPreference
    if ($nativeExit -ne 0) { throw "$StepName exited $nativeExit; inspect logs/$StepName.log" }
    "$(Get-Date -Format o) COMPLETE $StepName" | Add-Content 'logs\bootstrap-status.log'
}

try {
    Set-BootstrapState 'running' 'waiting-for-torch'
    Wait-Artifact 'C:\Dev\axg-cache\wheels\torch-2.11.0+cu128-cp312-cp312-win_amd64.whl'
    Invoke-PythonStep 'install-cuda' @('-m','pip','install','C:\Dev\axg-cache\wheels\torch-2.11.0+cu128-cp312-cp312-win_amd64.whl','torchvision','--index-url','https://download.pytorch.org/whl/cu128','--disable-pip-version-check')
    Invoke-PythonStep 'install-extra' @('-m','pip','install','accelerate','sentence-transformers==5.2.0','--disable-pip-version-check')
    Invoke-PythonStep 'gpu-check' @('-c',"import torch,json; assert torch.cuda.is_available(); x=torch.randn(1024,1024,device='cuda',dtype=torch.bfloat16); y=x@x; torch.cuda.synchronize(); print(json.dumps({'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(),'architectures':torch.cuda.get_arch_list(),'matmul_finite':bool(y.isfinite().all())})); assert y.isfinite().all()")
    & $pythonExe -m pip freeze *> 'logs\environment-freeze.txt'
    Wait-Artifact 'C:\Dev\AXG-Reasoner\data\public_cook4d\8_3.zip'
    Invoke-PythonStep 'prepare-public-data' @('prepare_public_data.py','--caption-stride','1')
    Wait-Artifact 'C:\Dev\axg-cache\Qwen2.5-VL-7B-Instruct\download_provenance.json'
    Invoke-PythonStep 'baseline-inference' @('-u','local_inference.py','--manifest','output\local7b\baseline_requests.json','--output','output\local7b\baseline_results')
    Invoke-PythonStep 'caption-inference' @('-u','local_inference.py','--manifest','output\local7b\caption_requests.json','--output','output\local7b\caption_results','--max-new-tokens','112')
    "$(Get-Date -Format o) BASELINE_AND_CAPTIONS_READY; continue graph construction" | Add-Content 'logs\bootstrap-status.log'
    Set-BootstrapState 'ready' 'BASELINE_AND_CAPTIONS_READY'
}
catch {
    "$(Get-Date -Format o) FAILED: $_" | Add-Content 'logs\bootstrap-status.log'
    Set-BootstrapState 'failed' ([string]$_)
    exit 1
}
