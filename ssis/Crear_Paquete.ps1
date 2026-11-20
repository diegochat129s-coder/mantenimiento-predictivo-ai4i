[CmdletBinding()]
param(
    [string]$Config = (Join-Path $PSScriptRoot '..\config\sqlserver.local.json'),
    [string]$ManagedDts = ''
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if ($PSVersionTable.PSEdition -eq 'Core') { throw 'Ejecuta este archivo con Windows PowerShell 5.1 (powershell.exe).' }
if (-not (Test-Path -LiteralPath $Config)) { throw 'Primero crea config/sqlserver.local.json.' }
$settings = Get-Content -LiteralPath $Config -Raw -Encoding UTF8 | ConvertFrom-Json
$python = (Get-Command $settings.python -ErrorAction Stop).Source
if (-not $ManagedDts) {
    $candidates = @()
    foreach ($folder in @("$env:ProgramFiles\Microsoft SQL Server","${env:ProgramFiles(x86)}\Microsoft SQL Server")) {
        if (Test-Path -LiteralPath $folder) {
            $candidates += Get-ChildItem -LiteralPath $folder -Filter Microsoft.SqlServer.ManagedDTS.dll -Recurse -ErrorAction SilentlyContinue
        }
    }
    $found = $candidates | Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $found) { throw 'Falta el runtime o SDK de SSIS. Instálalo y vuelve a ejecutar Crear_Paquete.ps1.' }
    $ManagedDts = $found.FullName
}
Add-Type -Path $ManagedDts
$package = New-Object Microsoft.SqlServer.Dts.Runtime.Package
$package.Name = 'AI4I_Carga_Full'
$package.Description = 'CSV AI4I, fechas simuladas, staging, publicación FULL transaccional y verificación.'
$package.ProtectionLevel = [Microsoft.SqlServer.Dts.Runtime.DTSProtectionLevel]::DontSaveSensitive
$package.MaximumErrorCount = 1
$package.MaxConcurrentExecutables = 1
$application = New-Object Microsoft.SqlServer.Dts.Runtime.Application
$ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$runner = Join-Path $root 'scripts\sqlserver\Datamart.ps1'
$specs = @(
    @{Name='Preparar tablas y procedimiento'; Exe=$ps; Args="-NoProfile -File `"$runner`" -Paso Inicializar -Config `"$Config`""},
    @{Name='Extraer CSV y transformar fechas'; Exe=$python; Args="`"$(Join-Path $root 'src\etl_sqlserver.py')`" --raiz `"$root`""},
    @{Name='Cargar staging con SqlBulkCopy'; Exe=$ps; Args="-NoProfile -File `"$runner`" -Paso Staging -Config `"$Config`""},
    @{Name='Publicar modelo estrella FULL'; Exe=$ps; Args="-NoProfile -File `"$runner`" -Paso Publicar -Config `"$Config`""},
    @{Name='Verificar conteos y ejecución'; Exe=$ps; Args="-NoProfile -File `"$runner`" -Paso Verificar -Config `"$Config`""}
)
$previous = $null
foreach ($spec in $specs) {
    $task = $package.Executables.Add('STOCK:ExecuteProcessTask')
    $task.Name = $spec.Name
    $task.FailPackageOnFailure = $true
    $task.Properties['Executable'].SetValue($task,$spec.Exe)
    $task.Properties['Arguments'].SetValue($task,$spec.Args)
    if ($spec.Name -ne 'Preparar tablas y procedimiento') {
        $flag = if ($spec.Exe -eq $python) { ' --carga-id ' } else { ' -CargaId ' }
        $literal = ($spec.Args + $flag).Replace('\','\\').Replace('"','\"')
        $task.SetExpression('Arguments',('"' + $literal + '" + @[System::ExecutionInstanceGUID]'))
    }
    $task.Properties['WorkingDirectory'].SetValue($task,$root)
    $task.Properties['FailTaskIfReturnCodeIsNotSuccessValue'].SetValue($task,$true)
    $task.Properties['SuccessValue'].SetValue($task,0)
    $task.Properties['TimeOut'].SetValue($task,900)
    $task.Properties['TerminateProcessAfterTimeOut'].SetValue($task,$true)
    if ($previous) {
        $link = $package.PrecedenceConstraints.Add($previous,$task)
        $link.Value = [Microsoft.SqlServer.Dts.Runtime.DTSExecResult]::Success
    }
    $previous = $task
}
$output = Join-Path $PSScriptRoot 'AI4I_Carga_Full.dtsx'
$application.SaveToXml($output,$package,$null)
$loaded = $application.LoadPackage($output,$null)
if ($loaded.Executables.Count -ne 5 -or $loaded.PrecedenceConstraints.Count -ne 4) {
    throw 'El paquete no conserva sus cinco tareas y cuatro enlaces.'
}
Write-Host "Paquete SSIS creado y releído: $output"
Write-Host 'Abre un proyecto Integration Services en Visual Studio y agrega este .dtsx como paquete existente.'
Write-Host 'La ejecución del paquete publica la carga. La generación por sí sola no la ejecuta.'
