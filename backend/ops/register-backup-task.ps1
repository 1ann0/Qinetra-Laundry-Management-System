# Registers a daily task only after the owner has supplied private configuration and closing time.
param(
    [Parameter(Mandatory)][string]$PythonExecutable,
    [Parameter(Mandatory)][string]$ConfigFile,
    [Parameter(Mandatory)][string]$DailyTime
)
$ErrorActionPreference = 'Stop'
$pythonPath = (Resolve-Path -LiteralPath $PythonExecutable).Path
$configPath = (Resolve-Path -LiteralPath $ConfigFile).Path
$backendRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($pythonPath.Contains('"') -or $configPath.Contains('"')) { throw 'Use paths without quotation marks.' }
$runTime = [datetime]::ParseExact($DailyTime, 'HH:mm', [Globalization.CultureInfo]::InvariantCulture)
$taskName = 'QLMS-Pilot-Encrypted-Backup'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) { throw 'A backup task already exists. Review it before replacing it.' }
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "-m ops.backup_job --config `"$configPath`"" -WorkingDirectory $backendRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $runTime
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
Write-Output 'Daily task registered. This computer must be awake, connected and signed in. Test a missed run and remote cloud upload before relying on it.'
