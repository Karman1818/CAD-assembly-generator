param(
    [string]$StepFile = "C:\Users\MarceliKarman\Desktop\CAD-assembly-generator\backend\storage\f17f4d31-e0ce-4e5d-b667-a2decbe7ae92.step",
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://127.0.0.1:3000",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
$BackendPython = Join-Path $RepoRoot "backend\venv\Scripts\python.exe"
$LogDir = Join-Path $RepoRoot "run-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$backendProc = $null
$frontendProc = $null

function Stop-ListenerOnPort {
    param([int]$Port)

    $lines = netstat -ano -p tcp | Select-String ":$Port "
    foreach ($line in $lines) {
        $text = ($line.ToString() -replace "\s+", " ").Trim()
        if ($text -notmatch "LISTENING") {
            continue
        }

        $parts = $text.Split(" ")
        $listenerPid = [int]$parts[-1]
        if ($listenerPid -gt 0) {
            try {
                Stop-Process -Id $listenerPid -Force -ErrorAction Stop
            } catch {
                Write-Warning "Could not stop PID $listenerPid on port ${Port}: $($_.Exception.Message)"
            }
        }
    }
}

function Wait-Url {
    param(
        [string]$Url,
        [int]$TimeoutSec = 60,
        [int]$RequestTimeoutSec = 20
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            return Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec $RequestTimeoutSec
        } catch {
            Start-Sleep -Milliseconds 1200
        }
    }

    throw "Timeout waiting for $Url"
}

function Read-SseEvents {
    param(
        [string]$Url,
        [int]$TimeoutSec = 240
    )

    $response = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec $TimeoutSec
    $events = @()

    foreach ($line in ($response.Content -split "`n")) {
        if ($line -like "data:*") {
            $payload = $line.Substring(5).Trim()
            if ($payload) {
                $events += ($payload | ConvertFrom-Json)
            }
        }
    }

    return ,$events
}

try {
    if (-not (Test-Path $StepFile)) {
        throw "STEP file not found: $StepFile"
    }

    Stop-ListenerOnPort -Port $BackendPort
    Stop-ListenerOnPort -Port $FrontendPort

    $backendOut = Join-Path $LogDir "backend.e2e.out.log"
    $backendErr = Join-Path $LogDir "backend.e2e.err.log"
    $frontendOut = Join-Path $LogDir "frontend.e2e.out.log"
    $frontendErr = Join-Path $LogDir "frontend.e2e.err.log"
    Remove-Item $backendOut, $backendErr, $frontendOut, $frontendErr -Force -ErrorAction SilentlyContinue

    $backendProc = Start-Process `
        -FilePath $BackendPython `
        -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "$BackendPort") `
        -WorkingDirectory $RepoRoot `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr `
        -PassThru

    $frontendProc = Start-Process `
        -FilePath "node.exe" `
        -ArgumentList @(".\node_modules\next\dist\bin\next", "dev", "--hostname", "127.0.0.1", "--port", "$FrontendPort") `
        -WorkingDirectory $FrontendDir `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr `
        -PassThru

    $backendRoot = Wait-Url -Url "$BackendUrl/" -TimeoutSec 30
    $frontendRoot = Wait-Url -Url "$FrontendUrl/" -TimeoutSec 120 -RequestTimeoutSec 30

    $uploadJson = & curl.exe -s -X POST -F "file=@$StepFile" "$BackendUrl/api/step/upload"
    $upload = $uploadJson | ConvertFrom-Json
    $jobId = $upload.job_id
    if (-not $jobId) {
        throw "Upload did not return a job_id"
    }

    $events = Read-SseEvents -Url "$BackendUrl/api/step/progress/$jobId/stream" -TimeoutSec 300
    $lastEvent = $events | Select-Object -Last 1
    if (-not $lastEvent -or $lastEvent.status -ne "completed") {
        throw "STEP processing failed: $($lastEvent.message)"
    }

    $parts = Invoke-RestMethod -Method Get -Uri "$BackendUrl/api/files/${jobId}_parts.json"
    $instructions = Invoke-RestMethod -Method Post -Uri "$BackendUrl/api/assembly/generate/$jobId"
    $savedInstructions = Invoke-RestMethod -Method Get -Uri "$BackendUrl/api/assembly/instructions/$jobId"
    $glb = Invoke-WebRequest -UseBasicParsing "$BackendUrl$($lastEvent.result_model_url)" -TimeoutSec 30
    $scene = Invoke-WebRequest -UseBasicParsing "$BackendUrl$($instructions.steps[0].sceneSvgUrl)" -TimeoutSec 30
    $pdf = Invoke-WebRequest -UseBasicParsing "$BackendUrl$($instructions.pdfUrl)" -TimeoutSec 30

    [pscustomobject]@{
        backend_status = $backendRoot.StatusCode
        frontend_status = $frontendRoot.StatusCode
        uploaded_file = [System.IO.Path]::GetFileName($StepFile)
        job_id = $jobId
        sse_messages = ($events | ForEach-Object { "{0}%:{1}" -f $_.progress, $_.message })
        model_status = $glb.StatusCode
        unique_parts = $parts.Count
        total_quantity = ($parts | Measure-Object -Property quantity -Sum).Sum
        instruction_mode = $instructions.generationMode
        instruction_warning = $instructions.generationWarning
        instruction_steps = $instructions.steps.Count
        saved_instruction_steps = $savedInstructions.steps.Count
        scene_status = $scene.StatusCode
        pdf_status = $pdf.StatusCode
        pdf_url = $instructions.pdfUrl
        scene_url = $instructions.steps[0].sceneSvgUrl
        backend_stdout_log = $backendOut
        backend_stderr_log = $backendErr
        frontend_stdout_log = $frontendOut
        frontend_stderr_log = $frontendErr
    } | ConvertTo-Json -Depth 6
}
finally {
    foreach ($proc in @($backendProc, $frontendProc)) {
        if ($proc -and -not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force
        }
    }
}
