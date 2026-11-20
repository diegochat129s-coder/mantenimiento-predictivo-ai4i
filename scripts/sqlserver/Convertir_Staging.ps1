function ConvertTo-StagingTable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][object[]]$Records,
        [Parameter(Mandatory=$true)][Guid]$CargaId
    )
    if ($Records.Count -eq 0) { throw 'Staging no puede estar vacío.' }
    if ('carga_id' -notin $Records[0].PSObject.Properties.Name) { throw 'Falta carga_id en staging.' }
    $table = New-Object System.Data.DataTable
    try {
        foreach ($name in $Records[0].PSObject.Properties.Name) {
            $type = if ($name -eq 'carga_id') { [Guid] } else { [string] }
            [void]$table.Columns.Add($name,$type)
        }
        foreach ($record in $Records) {
            $rowId = [Guid]::Parse([string]$record.carga_id)
            if ($rowId -ne $CargaId) { throw 'La fila pertenece a otra ejecución.' }
            $row = $table.NewRow()
            foreach ($column in $table.Columns) {
                if ($column.ColumnName -eq 'carga_id') {
                    $row[$column.ColumnName] = $rowId
                } else {
                    $row[$column.ColumnName] = $record.($column.ColumnName)
                }
            }
            $table.Rows.Add($row)
        }
        # Evitar que PowerShell enumere las filas al devolver el DataTable.
        return ,$table
    } catch { $table.Dispose(); throw }
}
