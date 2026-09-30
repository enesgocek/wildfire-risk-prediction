param([string]$PythonExe = "")
$ErrorActionPreference = "Stop"
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCommand) {
        $uvExe = $uvCommand.Source
    } elseif (Test-Path -LiteralPath '.venv\Scripts\uv.exe') {
        $uvExe = (Resolve-Path -LiteralPath '.venv\Scripts\uv.exe').Path
    } else {
        if (-not $PythonExe) {
            $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
            if (-not $pythonCommand) {
                throw 'Install uv or Python 3.12, or pass -PythonExe with the Python 3.12 executable.'
            }
            $PythonExe = $pythonCommand.Source
        }
        & $PythonExe -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 required"'
        if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
        & $PythonExe -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
        & '.\.venv\Scripts\python.exe' -m pip install uv==0.12.21
        if ($LASTEXITCODE -ne 0) { throw 'uv installation failed.' }
        $uvExe = (Resolve-Path -LiteralPath '.venv\Scripts\uv.exe').Path
    }
    $arguments = @('sync', '--locked', '--cache-dir', 'outputs/cache/uv')
    if ($PythonExe) { $arguments += @('--python', $PythonExe) }
    & $uvExe @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Locked environment installation failed.' }
    if (-not (Test-Path -LiteralPath '.env')) {
        Copy-Item -LiteralPath '.env.example' -Destination '.env'
    }
    Write-Host 'Environment ready. Select .venv\Scripts\python.exe in Antigravity.'
} finally {
    Pop-Location
}
