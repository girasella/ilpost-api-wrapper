param(
    [Parameter(Mandatory = $true)]
    [string]$Token
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Cleaning previous build artifacts..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build

Write-Host "Building package..."
python -m build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Uploading to PyPI..."
$env:TWINE_PASSWORD = $Token
twine upload -u __token__ dist/*
$uploadExit = $LASTEXITCODE
Remove-Item Env:TWINE_PASSWORD

exit $uploadExit
