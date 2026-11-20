[CmdletBinding()]
param(
    [ValidateSet('Inicializar','Staging','Publicar','Verificar','Todo')]
    [string]$Paso = 'Todo',
    [string]$Config = '',
    [string]$CargaId = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if (-not $Config) { $Config = Join-Path $root 'config\sqlserver.local.json' }
if (-not (Test-Path -LiteralPath $Config)) { throw "Configura el servidor en $Config" }
$settings = Get-Content -LiteralPath $Config -Raw -Encoding UTF8 | ConvertFrom-Json
if ($settings.base -notmatch '^[A-Za-z][A-Za-z0-9_]{0,63}$') { throw 'Nombre de base inválido.' }
if ($settings.base -in @('master','model','msdb','tempdb')) { throw 'Se requiere una base de proyecto.' }
Add-Type -AssemblyName System.Data
. (Join-Path $PSScriptRoot 'Convertir_Staging.ps1')
$builder = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
$builder['Data Source'] = $settings.servidor
$builder['Integrated Security'] = $true
$builder['Encrypt'] = [bool]$settings.cifrar
$builder['TrustServerCertificate'] = [bool]$settings.confiar_certificado_local
$builder['Connect Timeout'] = 15
if ($builder['TrustServerCertificate'] -and $settings.servidor -notmatch '^(\.|localhost|127\.0\.0\.1)(\\[^;]+)?$') {
    throw 'La confianza explícita en un certificado de desarrollo se limita al servidor local.'
}
function Open-Database([string]$Database) {
    $builder['Initial Catalog'] = $Database
    $connection = New-Object System.Data.SqlClient.SqlConnection $builder.ConnectionString
    $connection.Open()
    return $connection
}
function Invoke-CommandSql($Connection, [string]$Text) {
    $command = $Connection.CreateCommand()
    $command.CommandText = $Text
    $command.CommandTimeout = 180
    try { [void]$command.ExecuteNonQuery() } finally { $command.Dispose() }
}
function Read-Run {
    if ($CargaId) {
        $id = ([Guid]$CargaId).ToString()
        $pointer = [pscustomobject]@{ directorio=(Join-Path $root "data\processed\sqlserver\$id"); carga_id=$id }
    } else {
        $pointer = Get-Content -LiteralPath (Join-Path $root 'data\processed\sqlserver\actual.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    $directory = [IO.Path]::GetFullPath($pointer.directorio)
    $expected = [IO.Path]::GetFullPath((Join-Path $root 'data\processed\sqlserver')) + [IO.Path]::DirectorySeparatorChar
    if (-not $directory.StartsWith($expected,[StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta de ejecución inválida.' }
    $manifest = Get-Content -LiteralPath (Join-Path $directory 'manifiesto.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.carga_id -ne $pointer.carga_id) { throw 'Los identificadores de ejecución difieren.' }
    $stageHash = (Get-FileHash -LiteralPath (Join-Path $directory 'staging.csv') -Algorithm SHA256).Hash
    $rawHash = (Get-FileHash -LiteralPath (Join-Path $root 'data\raw\ai4i2020.csv') -Algorithm SHA256).Hash
    if ($stageHash -ne $manifest.sha256_staging -or $rawHash -ne $manifest.sha256_original) { throw 'La huella del archivo cambió. Prepare otra carga.' }
    return @{ Directory=$directory; Manifest=$manifest }
}
if ($Paso -in @('Inicializar','Todo')) {
    $connection = Open-Database 'master'
    try { Invoke-CommandSql $connection "IF DB_ID(N'$($settings.base)') IS NULL CREATE DATABASE [$($settings.base)];" }
    finally { $connection.Dispose() }
    $connection = Open-Database $settings.base
    try {
        foreach ($file in @('01_crear_datamart.sql','02_carga_full.sql')) {
            Invoke-CommandSql $connection (Get-Content -LiteralPath (Join-Path $root "sql\sqlserver\$file") -Raw -Encoding UTF8)
        }
    } finally { $connection.Dispose() }
    Write-Host 'Tablas y procedimiento preparados.'
}
if ($Paso -eq 'Todo') {
    if (-not $CargaId) { $CargaId=[Guid]::NewGuid().ToString() }
    & $settings.python (Join-Path $root 'src\etl_sqlserver.py') '--raiz' $root '--carga-id' $CargaId
    if ($LASTEXITCODE -ne 0) { throw 'La preparación del CSV falló.' }
}
if ($Paso -in @('Staging','Todo')) {
    $run = Read-Run
    $manifest = $run.Manifest
    $records = @(Import-Csv -LiteralPath (Join-Path $run.Directory 'staging.csv') -Encoding UTF8)
    if ($records.Count -ne 10000) { throw 'El CSV preparado debe tener 10000 filas.' }
    $table = ConvertTo-StagingTable -Records $records -CargaId ([Guid]$manifest.carga_id)
    $connection = Open-Database $settings.base
    $transaction = $connection.BeginTransaction()
    $bulk = New-Object System.Data.SqlClient.SqlBulkCopy($connection,[System.Data.SqlClient.SqlBulkCopyOptions]::CheckConstraints,$transaction)
    try {
        $command = $connection.CreateCommand()
        $command.Transaction = $transaction
        $command.CommandText = 'IF EXISTS(SELECT 1 FROM auditoria.cargas WHERE carga_id=@id) THROW 51008,''La carga ya se publicó.'',1; DELETE stg.operacion WHERE carga_id=@id;'
        [void]$command.Parameters.Add('@id',[System.Data.SqlDbType]::UniqueIdentifier)
        $command.Parameters['@id'].Value = [Guid]$manifest.carga_id
        [void]$command.ExecuteNonQuery()
        $command.Dispose()
        $bulk.DestinationTableName = 'stg.operacion'
        $bulk.BulkCopyTimeout = 180
        foreach ($column in $table.Columns) { [void]$bulk.ColumnMappings.Add($column.ColumnName,$column.ColumnName) }
        $bulk.WriteToServer($table)
        $transaction.Commit()
    } catch { $transaction.Rollback(); throw }
    finally { $bulk.Dispose(); $transaction.Dispose(); $connection.Dispose(); $table.Dispose() }
    Write-Host 'Staging preparado con 10000 filas.'
}
if ($Paso -in @('Publicar','Todo')) {
    $run = Read-Run
    $connection = Open-Database $settings.base
    $command = $connection.CreateCommand()
    try {
        $command.CommandType = [System.Data.CommandType]::StoredProcedure
        $command.CommandText = 'dm.usp_carga_full'
        $command.CommandTimeout = 180
        [void]$command.Parameters.Add('@carga_id',[System.Data.SqlDbType]::UniqueIdentifier)
        $command.Parameters['@carga_id'].Value = [Guid]$run.Manifest.carga_id
        [void]$command.Parameters.Add('@sha256_original',[System.Data.SqlDbType]::Char,64)
        $command.Parameters['@sha256_original'].Value = $run.Manifest.sha256_original
        [void]$command.ExecuteNonQuery()
    } finally { $command.Dispose(); $connection.Dispose() }
    Write-Host 'FULL publicado correctamente.'
}
if ($Paso -in @('Verificar','Todo')) {
    $run = Read-Run
    $connection = Open-Database $settings.base
    $command = $connection.CreateCommand()
    try {
        $command.CommandText = @'
SELECT COUNT(*) filas,SUM(estado_id) fallas,COUNT(DISTINCT tiempo_id) dias_con_datos,
 COUNT(DISTINCT carga_id) cargas_en_hechos,
 (SELECT COUNT(*) FROM dm.dim_tiempo) dias_calendario,
 (SELECT COUNT(*) FROM dm.fact_operacion WHERE carga_id=@id) filas_esta_carga
FROM dm.fact_operacion;
'@
        [void]$command.Parameters.Add('@id',[System.Data.SqlDbType]::UniqueIdentifier)
        $command.Parameters['@id'].Value = [Guid]$run.Manifest.carga_id
        $adapter = New-Object System.Data.SqlClient.SqlDataAdapter $command
        $table = New-Object System.Data.DataTable
        [void]$adapter.Fill($table)
        $row = $table.Rows[0]
        if ($row.filas -ne 10000 -or $row.fallas -ne 339 -or $row.dias_con_datos -ne 200 -or $row.dias_calendario -ne 365 -or $row.filas_esta_carga -ne 10000 -or $row.cargas_en_hechos -ne 1) {
            throw 'Los conteos finales o la ejecución publicada no coinciden con AI4I.'
        }
        $evidence = [ordered]@{
            estado='sqlserver_verificado'; carga_id=$run.Manifest.carga_id
            servidor=$settings.servidor; base=$settings.base
            fecha_verificacion_utc=[DateTime]::UtcNow.ToString('o')
            filas=[int]$row.filas; fallas=[int]$row.fallas
            dias_con_datos=[int]$row.dias_con_datos; dias_calendario=[int]$row.dias_calendario
        }
        $results = Join-Path $root 'results\sqlserver'
        New-Item -ItemType Directory -Path $results -Force | Out-Null
        $evidence | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $results 'ultima_verificacion.json') -Encoding UTF8
        $evidence | Format-List
        $adapter.Dispose(); $table.Dispose()
    } finally { $command.Dispose(); $connection.Dispose() }
}
