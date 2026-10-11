# Human-operated local tooling setup; no QLMS app or cloud-data changes.
param([switch]$ValidateOnly)

$ErrorActionPreference = 'Stop'
$qlmsToolsRoot = Join-Path $env:LOCALAPPDATA 'QLMS-tools'
$qlmsSdkRoot = Join-Path $qlmsToolsRoot 'google-cloud-sdk'
$qlmsCliPath = Join-Path $qlmsSdkRoot 'bin\gcloud.cmd'
$qlmsNodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$qlmsNpmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
$qlmsCodexCommand = Get-Command codex.cmd -ErrorAction SilentlyContinue
$qlmsTarCommand = Get-Command tar.exe -ErrorAction SilentlyContinue

if ($ValidateOnly) {
    if (-not $qlmsNodeCommand -or -not $qlmsNpmCommand -or -not $qlmsCodexCommand -or -not $qlmsTarCommand) {
        throw 'Node, npm, Codex CLI and Windows tar are required.'
    }
    Write-Output 'PASS: setup prerequisites found; validation made no changes and used no credentials.'
    exit 0
}

# Credentials stay in the human's terminal, never an agent's captured output.
if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) {
    throw 'Run this setup in your own interactive PowerShell outside Codex.'
}
if (-not $qlmsNodeCommand -or -not $qlmsNpmCommand -or -not $qlmsCodexCommand -or -not $qlmsTarCommand) {
    Write-Output 'FAIL: Node, npm, Codex CLI or Windows tar is missing. No sign-in was started.'
    exit 1
}

$qlmsStage = 'download and installation'
try {
    New-Item -ItemType Directory -Path $qlmsToolsRoot -Force | Out-Null
    if (-not (Test-Path -LiteralPath $qlmsCliPath)) {
        $qlmsArchiveName = 'google-cloud-sdk-588.0.0-windows-x86_64-bundled-python.zip'
        $qlmsArchivePath = Join-Path $qlmsToolsRoot $qlmsArchiveName
        $qlmsProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
        $qlmsExistingArchive = Join-Path (Join-Path $qlmsProjectRoot 'tmp') $qlmsArchiveName
        if (Test-Path -LiteralPath $qlmsExistingArchive) { $qlmsArchivePath = $qlmsExistingArchive }
        if (-not (Test-Path -LiteralPath $qlmsArchivePath)) {
            Write-Host 'Downloading the official Google Cloud CLI. No billing or Google sign-in is involved.'
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -UseBasicParsing -Uri ('https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/' + $qlmsArchiveName) -OutFile $qlmsArchivePath -TimeoutSec 300
        }
        if ((Get-FileHash -LiteralPath $qlmsArchivePath -Algorithm SHA256).Hash -ne '9E00E3C9B042F732E29EB7CA6095FDB44BDA03938013274A148B5C5F95A6EC92') {
            throw 'Official CLI checksum mismatch.'
        }
        Write-Host 'Extracting the verified CLI archive. This can take a few minutes.'
        # Windows tar cannot create six auxiliary gsutil links; ZIP completes missing entries.
        $qlmsPriorErrorPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $qlmsExtractionOutput = & $qlmsTarCommand.Source -xf $qlmsArchivePath -C $qlmsToolsRoot 2>&1
        $ErrorActionPreference = $qlmsPriorErrorPreference
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $qlmsSdkPrefix = [IO.Path]::GetFullPath($qlmsSdkRoot) + '\'
        $qlmsSdkZip = [IO.Compression.ZipFile]::OpenRead($qlmsArchivePath)
        try {
            foreach ($qlmsEntry in $qlmsSdkZip.Entries) {
                if (-not $qlmsEntry.Name) { continue }
                $qlmsDestination = [IO.Path]::GetFullPath((Join-Path $qlmsToolsRoot $qlmsEntry.FullName))
                if (-not $qlmsDestination.StartsWith($qlmsSdkPrefix, [StringComparison]::OrdinalIgnoreCase)) {
                    throw 'Unexpected archive destination.'
                }
                if (-not [IO.File]::Exists($qlmsDestination)) {
                    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($qlmsDestination)) | Out-Null
                    [IO.Compression.ZipFileExtensions]::ExtractToFile($qlmsEntry, $qlmsDestination, $false)
                }
            }
        } finally { $qlmsSdkZip.Dispose() }
    }

    $qlmsStage = 'CLI verification'
    $env:CLOUDSDK_CONFIG = Join-Path $qlmsToolsRoot 'gcloud-install-check'
    $env:CLOUDSDK_CORE_DISABLE_USAGE_REPORTING = 'true'
    $qlmsCliVersion = & $qlmsCliPath version 2>&1
    if ($LASTEXITCODE -ne 0 -or ($qlmsCliVersion -join "`n") -notmatch 'Google Cloud SDK 588\.0\.0') {
        throw 'CLI verification failed or an unexpected version is installed.'
    }
    $qlmsStage = 'MCP package installation'
    $qlmsPackageRoot = Join-Path $qlmsToolsRoot 'gcloud-mcp'
    & $qlmsNpmCommand.Source install --prefix $qlmsPackageRoot --save-exact --ignore-scripts --no-fund --no-audit '@google-cloud/gcloud-mcp@0.5.3'
    if ($LASTEXITCODE -ne 0) { throw 'MCP package installation failed.' }
    $qlmsBundle = Join-Path $qlmsPackageRoot 'node_modules\@google-cloud\gcloud-mcp\dist\bundle.js'
    if (-not (Test-Path -LiteralPath $qlmsBundle)) { throw 'MCP entry point missing.' }

    $qlmsStage = 'private directory and command policy'
    $qlmsPrivatePath = Join-Path $qlmsToolsRoot 'gcloud-private'
    if (-not (Test-Path -LiteralPath $qlmsPrivatePath)) {
        New-Item -ItemType Directory -Path $qlmsPrivatePath | Out-Null
        $qlmsCurrentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
        $qlmsPrivateAcl = New-Object Security.AccessControl.DirectorySecurity
        $qlmsPrivateAcl.SetAccessRuleProtection($true, $false)
        $qlmsPrivateAcl.SetOwner($qlmsCurrentSid)
        $qlmsInheritance = [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit'
        $qlmsPropagation = [Security.AccessControl.PropagationFlags]::None
        $qlmsAllow = [Security.AccessControl.AccessControlType]::Allow
        $qlmsPrivateAcl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($qlmsCurrentSid, 'FullControl', $qlmsInheritance, $qlmsPropagation, $qlmsAllow)))
        $qlmsSystemSid = New-Object Security.Principal.SecurityIdentifier('S-1-5-18')
        $qlmsPrivateAcl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($qlmsSystemSid, 'FullControl', $qlmsInheritance, $qlmsPropagation, $qlmsAllow)))
        Set-Acl -LiteralPath $qlmsPrivatePath -AclObject $qlmsPrivateAcl
    }
    $qlmsPolicyPath = Join-Path $qlmsToolsRoot 'gcloud-mcp-allowlist.json'
    $qlmsPolicyJson = @{ allow = @('version', 'projects describe', 'services list', 'services enable') } | ConvertTo-Json
    [IO.File]::WriteAllText($qlmsPolicyPath, $qlmsPolicyJson, (New-Object Text.UTF8Encoding($false)))

    $qlmsStage = 'Codex registration'
    $qlmsArgs = @('mcp', 'add', 'gcloud-qlms', '--env', ('PATH=' + (Join-Path $qlmsSdkRoot 'bin') + ';' + $env:PATH),
        '--env', ('CLOUDSDK_CONFIG=' + $qlmsPrivatePath), '--env', 'CLOUDSDK_CORE_PROJECT=qlms-backup-automation',
        '--env', 'CLOUDSDK_CORE_ACCOUNT=qinetraian@gmail.com', '--env', 'CLOUDSDK_CORE_DISABLE_USAGE_REPORTING=true',
        '--env', 'CLOUDSDK_CORE_DISABLE_PROMPTS=true', '--', $qlmsNodeCommand.Source, $qlmsBundle, '--config', $qlmsPolicyPath)
    & $qlmsCodexCommand.Source @qlmsArgs
    if ($LASTEXITCODE -ne 0) { throw 'Codex registration failed.' }
    Write-Output 'PASS: CLI installed in this Windows environment; limited MCP registered. Starting private sign-in.'

    $qlmsStage = 'private Google sign-in'
    $env:CLOUDSDK_CONFIG = $qlmsPrivatePath
    Write-Host 'Keep Google sign-in and this terminal private. Do not send codes, URLs, passwords or raw logs.'
    & $qlmsCliPath auth login 'qinetraian@gmail.com' --brief
    if ($LASTEXITCODE -ne 0) { throw 'Private sign-in did not complete.' }
    Write-Output 'PASS: private Google CLI sign-in completed. Restart Codex and continue the QLMS chat.'
} catch {
    Write-Output ('FAIL: Google Cloud MCP setup did not complete at ' + $qlmsStage + '. Report only this line; keep private output out of chat.')
    exit 1
}
