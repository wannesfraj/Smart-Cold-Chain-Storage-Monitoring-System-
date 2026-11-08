param(
    [ValidateSet('Build', 'Test', 'Pack', 'All')]
    [string]$Action = 'Build'
)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    if ($Action -in @('Build', 'All')) {
        python tools/build_project.py
        if ($LASTEXITCODE -ne 0) { throw 'La compilation a échoué.' }
    }
    if ($Action -in @('Test', 'All')) {
        python tools/test_project.py
        if ($LASTEXITCODE -ne 0) { throw 'Les tests ont échoué.' }
    }
    if ($Action -in @('Pack', 'All')) {
        python tools/package_project.py
        if ($LASTEXITCODE -ne 0) { throw "La création de l'archive a échoué." }
    }
} finally {
    Pop-Location
}
