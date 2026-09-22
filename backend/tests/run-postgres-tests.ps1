# Creates one disposable PostgreSQL container; never uses the project's database URL.
param([string]$PythonExecutable = '')

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $PythonExecutable) {
    $PythonExecutable = Join-Path $repoRoot 'backend/venv/Scripts/python.exe'
}
# Fail before creating a container if the selected virtual environment is broken.
& $PythonExecutable --version
if ($LASTEXITCODE -ne 0) { throw 'Choose a working Python environment with -PythonExecutable.' }
$containerName = 'qlms-save-test-' + [guid]::NewGuid().ToString('N')
$containerCreated = $false
$previousEnv = @{}
foreach ($name in @('DATABASE_URL', 'SECRET_KEY', 'QLMS_TEST_DATABASE_URL')) {
    $previousEnv[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
$testExitCode = 1
try {
    & docker version --format '{{.Server.Version}}'
    if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop and wait for the engine to run.' }
    & docker run --detach --rm --name $containerName --publish '127.0.0.1:55432:5432' --env 'POSTGRES_DB=qlms_test' --env 'POSTGRES_PASSWORD=qlms-local-test' postgres:17
    if ($LASTEXITCODE -ne 0) { throw 'The test database could not start. Check that port 55432 is free.' }
    $containerCreated = $true
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        & docker exec $containerName pg_isready -U postgres -d qlms_test *> $null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw 'The disposable database did not become ready.' }
    $env:DATABASE_URL = 'sqlite://'
    $env:SECRET_KEY = 'local-test-fixture-only-at-least-thirty-two-bytes'
    $env:QLMS_TEST_DATABASE_URL = 'postgresql://postgres:qlms-local-test@127.0.0.1:55432/qlms_test'
    Push-Location (Join-Path $repoRoot 'backend')
    try {
        & $PythonExecutable -m unittest discover -s tests
        $testExitCode = $LASTEXITCODE
    } finally { Pop-Location }
} finally {
    if ($containerCreated) { & docker stop $containerName | Out-Null }
    foreach ($name in $previousEnv.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnv[$name], 'Process')
    }
}
exit $testExitCode
