<#
Small helper to set up and run OpenHands locally on Windows (PowerShell)
Usage:
  From repo root (d:\Openhands\OpenHands):
    .\scripts\run_local_windows.ps1            # interactive CLI (default)
    .\scripts\run_local_windows.ps1 -Serve     # start GUI server (serve command)

What it does:
  - creates/activates .venv
  - installs poetry if missing
  - sets SKIP_VSCODE_BUILD=1 to avoid VSCode build problems on Windows
  - optionally sets SKIP_DEPENDENCY_CHECK=1 (default: true) to bypass jupyter/libtmux checks
  - sets RUNTIME=local so OpenHands uses the LocalRuntime
  - runs `poetry install` then launches OpenHands

Notes:
  - Run in PowerShell with appropriate execution policy. If scripts are blocked, run as Administrator and set `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
  - You can edit the script to disable SKIP_DEPENDENCY_CHECK if you want dependency checks.
#>

param(
    [switch]$Serve,
    [switch]$NoSkipDependencyCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }

# Ensure we are in the repo root; if not, warn but continue
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "WARNING: pyproject.toml not found in current directory. Please run this script from the OpenHands repo root." -ForegroundColor Yellow
}

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found in PATH. Please install Python 3.12 and ensure 'python' is on PATH." -ForegroundColor Red
    exit 1
}

# Create virtualenv if missing
if (-not (Test-Path ".venv")) {
    Write-Info "Creating virtual environment .venv..."
    python -m venv .venv
} else {
    Write-Info ".venv already exists"
}

# Activate venv in this session
Write-Info "Activating .venv..."
. .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Info "Ensuring pip is up-to-date"
python -m pip install --upgrade pip

# Ensure poetry
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Info "Poetry not found; installing poetry via pip"
    pip install poetry
} else {
    Write-Info "Poetry detected"
}

# Set environment variables used by OpenHands for local runs
# Avoid VSCode build step on Windows
$env:SKIP_VSCODE_BUILD = '1'
# Skip dependency checks by default on Windows (can be disabled with -NoSkipDependencyCheck)
if (-not $NoSkipDependencyCheck) {
    $env:SKIP_DEPENDENCY_CHECK = '1'
    Write-Info "SKIP_DEPENDENCY_CHECK=1"
} else {
    Write-Info "SKIP_DEPENDENCY_CHECK not set (dependency checks will run)"
}
# Tell OpenHands to use local runtime
$env:RUNTIME = 'local'

Write-Info "SKIP_VSCODE_BUILD=1, RUNTIME=local set in environment"

# Install dependencies
Write-Info "Running 'poetry install' (this may take a while the first time)"
poetry install

# Run OpenHands
if ($Serve) {
    Write-Info "Starting OpenHands server (serve)..."
    poetry run openhands serve
} else {
    Write-Info "Starting OpenHands CLI (interactive)..."
    poetry run openhands
}
