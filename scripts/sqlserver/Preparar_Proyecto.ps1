[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Servidor,
    [string]$Base = 'MantenimientoPredictivoDM',
    [string]$Python = 'python.exe',
    [switch]$CertificadoLocal,
    [switch]$CrearPaquete,
    [switch]$EjecutarCarga
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$config=Join-Path $root 'config\sqlserver.local.json'
if (Test-Path -LiteralPath $config) { throw "Ya existe $config. Revísalo antes de reemplazar la configuración." }
$pythonExe=(Get-Command $Python -ErrorAction Stop).Source
$settings=[ordered]@{servidor=$Servidor;base=$Base;cifrar=$true;confiar_certificado_local=[bool]$CertificadoLocal;python=$pythonExe}
$settings | ConvertTo-Json | Set-Content -LiteralPath $config -Encoding UTF8
& $pythonExe (Join-Path $root 'scripts\generar_powerbi.py') --servidor $Servidor --base $Base
if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el proyecto Power BI.' }
if ($CrearPaquete) { & (Join-Path $root 'ssis\Crear_Paquete.ps1') -Config $config }
if ($EjecutarCarga) { & (Join-Path $PSScriptRoot 'Datamart.ps1') -Paso Todo -Config $config }
Write-Host "Configuración guardada en $config"
