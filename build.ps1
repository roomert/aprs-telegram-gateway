# Windows build. Settings live in build.toml.
# Usage: .\build.ps1 [-Label windows-x64]
param(
    [string]$Label = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "Python 3 was not found on PATH. Install Python 3.11+ and retry."
    }
    & python -m venv (Join-Path $ProjectRoot ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Could not create the build virtual environment." }
}

& $VenvPython -m pip install -q -r (Join-Path $ProjectRoot "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install build dependencies." }

$RuntimeRequirements = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path -LiteralPath $RuntimeRequirements -PathType Leaf) {
    & $VenvPython -m pip install -q -r $RuntimeRequirements
    if ($LASTEXITCODE -ne 0) { throw "Could not install application dependencies." }
}

$BuildArgs = @((Join-Path $ProjectRoot "build.py"))
if ($Label) { $BuildArgs += @("--label", $Label) }
& $VenvPython @BuildArgs
exit $LASTEXITCODE
