# Creates one disposable PostgreSQL container; never uses the project's database URL.
param([string]$PythonExecutable = '', [switch]$OperationsOnly, [string]$CloudClientImage = '')

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $PythonExecutable) {
    $PythonExecutable = Join-Path $repoRoot 'backend/venv/Scripts/python.exe'
}
# Fail before creating a container if the selected virtual environment is broken.
& $PythonExecutable --version
if ($LASTEXITCODE -ne 0) { throw 'Choose a working Python environment with -PythonExecutable.' }
$containerName = 'qlms-save-test-' + [guid]::NewGuid().ToString('N')
$postgresImage = 'postgres:17@sha256:67f41722b7a8cbdb868a44a4995c846eddfdc2973bccb291ce937dce88ad5675'
$containerCreated = $false
$previousEnv = @{}
foreach ($name in @('DATABASE_URL', 'SECRET_KEY', 'QLMS_TEST_DATABASE_URL', 'PYTHON_DOTENV_DISABLED')) {
    $previousEnv[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
$testExitCode = 1
try {
    & docker version --format '{{.Server.Version}}'
    if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop and wait for the engine to run.' }
    & docker run --detach --rm --name $containerName --publish '127.0.0.1:55432:5432' --env 'POSTGRES_DB=qlms_test' --env 'POSTGRES_PASSWORD=qlms-local-test' $postgresImage
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
    $env:PYTHON_DOTENV_DISABLED = '1'
    $env:SECRET_KEY = 'local-test-fixture-only-at-least-thirty-two-bytes'
    $env:QLMS_TEST_DATABASE_URL = 'postgresql://postgres:qlms-local-test@127.0.0.1:55432/qlms_test'
    Push-Location (Join-Path $repoRoot 'backend')
    try {
        if ($OperationsOnly) { $testExitCode = 0 }
        else {
            & $PythonExecutable -m unittest discover -s tests
            $testExitCode = $LASTEXITCODE
        }
        if ($testExitCode -eq 0) {
            & $PythonExecutable -m ops.rehearse_schema --container $containerName
            $testExitCode = $LASTEXITCODE
            if ($testExitCode -eq 0) {
                $recoveryArguments = @('-m', 'ops.rehearse_recovery', '--container', $containerName)
                if ($CloudClientImage) { $recoveryArguments += @('--client-image', $CloudClientImage) }
                & $PythonExecutable @recoveryArguments
                $testExitCode = $LASTEXITCODE
            }
        }
    } finally { Pop-Location }
} finally {
    if ($containerCreated) { & docker stop $containerName | Out-Null }
    foreach ($name in $previousEnv.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnv[$name], 'Process')
    }
}
exit $testExitCode
