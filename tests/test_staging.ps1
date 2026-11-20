$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type -AssemblyName System.Data
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $root 'scripts\sqlserver\Convertir_Staging.ps1')
$pointer = Get-Content -LiteralPath (Join-Path $root 'data\processed\sqlserver\actual.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$records = @(Import-Csv -LiteralPath (Join-Path $pointer.directorio 'staging.csv') -Encoding UTF8)
$id = [Guid]$pointer.carga_id
$table = ConvertTo-StagingTable -Records $records -CargaId $id
try {
    if ($table -isnot [System.Data.DataTable]) { throw 'No se devolvió un DataTable.' }
    if ($table.Rows.Count -ne 10000) { throw 'Se perdieron registros.' }
    if ($table.Columns['carga_id'].DataType -ne [Guid]) { throw 'El identificador no está tipado como GUID.' }
    foreach ($row in $table.Rows) {
        if ($row.carga_id -isnot [Guid] -or $row.carga_id -ne $id) { throw 'GUID distinto o convertido a texto.' }
    }
    foreach ($column in $table.Columns) {
        if ($column.ColumnName -ne 'carga_id' -and $column.DataType -ne [string]) { throw 'Cambió el contrato textual del resto de staging.' }
    }
    if ($table.Rows[0].udi -ne $records[0].udi -or $table.Rows[9999].torque_nm -ne $records[9999].torque_nm) { throw 'Se alteraron las mediciones.' }
} finally { $table.Dispose() }
foreach ($badId in @('no-es-un-guid',[Guid]::NewGuid().ToString())) {
    $bad = [pscustomobject]@{ carga_id=$badId; udi='1' }
    $rejected = $false
    try {
        $unexpected = ConvertTo-StagingTable -Records @($bad) -CargaId $id
        $unexpected.Dispose()
    } catch { $rejected = $true }
    if (-not $rejected) { throw 'Se aceptó un identificador inválido o de otra carga.' }
}
Write-Output 'OK: 10000 filas con GUID nativo, mediciones conservadas y cargas incorrectas rechazadas. No se ejecutó SQL.'
