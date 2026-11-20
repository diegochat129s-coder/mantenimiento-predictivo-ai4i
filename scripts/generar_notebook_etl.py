"""Genera el notebook explicativo y un CSV derivado sin modificar AI4I original."""
from pathlib import Path
import sys
import nbformat as nbf
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from etl_sqlserver import transformar


def generate():
    source = pd.read_csv(ROOT / 'data/raw/ai4i2020.csv')
    transformar(source).to_csv(ROOT / 'data/processed/ai4i_fechas_simuladas.csv', index=False)
    md = nbf.v4.new_markdown_cell
    code = nbf.v4.new_code_cell
    notebook = nbf.v4.new_notebook(cells=[
        md('''# ETL para SQL Server y SSIS
**Diego Salinas Laguna · AI4I 2020**

Este notebook demuestra la extracción y transformación. El procedimiento de publicación
está en `sql/sqlserver/02_carga_full.sql`. La carga SQL se ejecuta con SSIS o con
`scripts/sqlserver/Datamart.ps1`; este notebook no la publica automáticamente.

**Fechas simuladas para la práctica:** no son fechas originales de operación.'''),
        code('''from pathlib import Path
import sys, hashlib, json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

root = Path.cwd().resolve()
while not (root / 'src/etl_sqlserver.py').exists():
    if root == root.parent:
        raise FileNotFoundError('Abre Jupyter dentro de la carpeta completa del proyecto.')
    root = root.parent
sys.path.insert(0, str(root / 'src'))
from etl_sqlserver import transformar, preparar
original = root / 'data/raw/ai4i2020.csv'
huella_inicial = hashlib.sha256(original.read_bytes()).hexdigest()
datos = pd.read_csv(original)
print('Filas y columnas originales:', datos.shape)
display(datos.head())'''),
        md('''## 1. Revisar antes de cargar
Comprobamos valores faltantes, filas repetidas y etiquetas. Las discrepancias
no se corrigen sin una justificación del origen.'''),
        code('''calidad = pd.Series({
    'filas': len(datos),
    'columnas_originales': len(datos.columns),
    'valores_nulos': int(datos.isna().sum().sum()),
    'filas_duplicadas': int(datos.duplicated().sum()),
    'observaciones_con_falla': int(datos['Machine failure'].sum()),
    'discrepancias_etiquetas': int(datos['Machine failure'].ne(
        datos[['TWF','HDF','PWF','OSF','RNF']].max(axis=1)).sum()),
})
display(calidad.to_frame('valor'))
display(datos[['Air temperature [K]', 'Process temperature [K]',
               'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']].describe())'''),
        md('''## 2. Transformar y agregar fechas
`transformar` valida nombres, tipos, identificadores y rangos. Renombra columnas,
ordena por UDI y agrega claves de tipo y tiempo.

La fecha es `2026-01-01 + floor((UDI - 1) / 50)` días.
Repetir la carga conserva las mismas fechas. `tiempo_id` usa AAAAMMDD.'''),
        code('''procesados = transformar(datos)
display(procesados.loc[[0,49,50,99,9999],
    ['udi','product_id','tipo','tipo_id','fecha_operacion_simulada','tiempo_id']])
print('Desde:', procesados.fecha_operacion_simulada.min())
print('Hasta:', procesados.fecha_operacion_simulada.max())
print('Días con datos:', procesados.tiempo_id.nunique())
assert procesados.groupby('tiempo_id').size().eq(50).all()
assert transformar(datos.sample(frac=1, random_state=42)).equals(procesados)'''),
        md('''## 3. Visualizar el calendario de práctica
Las barras muestran el reparto de registros entre meses simulados. Julio es parcial.
La diferencia se debe a la regla de asignación, no a cambios reales de producción.'''),
        code('''mensual = procesados.assign(mes=procesados.fecha_operacion_simulada.str[:7])
resumen = mensual.groupby('mes').agg(observaciones=('udi','size'), fallas=('estado_id','sum'))
resumen['porcentaje_fallas'] = resumen.fallas / resumen.observaciones * 100
display(resumen)
ax = resumen.observaciones.plot.bar(color='#2563eb', figsize=(9,4), rot=0)
ax.set(title='Observaciones por mes: calendario simulado', xlabel='Mes simulado', ylabel='Observaciones')
plt.tight_layout()
plt.show()'''),
        md('''## 4. Preparar una ejecución independiente
`preparar` crea una carpeta por ejecución con CSV, staging, discrepancias y manifiesto.
Preparar archivos no acredita una carga SQL. SHA-256 comprueba que el original no cambió.'''),
        code('''ejecucion = preparar(root)
manifiesto = json.loads((ejecucion / 'manifiesto.json').read_text(encoding='utf-8'))
display(pd.Series(manifiesto).to_frame('valor'))
print('Archivos preparados:', sorted(p.name for p in ejecucion.iterdir()))
assert hashlib.sha256(original.read_bytes()).hexdigest() == huella_inicial
print('Original conservado sin cambios.')'''),
        md('''## 5. Publicar mediante SSIS y comprobar el Data Mart
Seguir `docs/INSTALACION_SQLSERVER_SSIS_POWERBI.md` para configurar el servidor y
generar el paquete. Sus cinco tareas preparan objetos, transforman CSV, cargan
staging, publican FULL y verifican.

`dm.fact_operacion` guarda 10,000 observaciones. `dm.dim_tipo`, `dm.dim_estado`
y `dm.dim_tiempo` permiten filtrar por tipo, estado y fecha. Hay 365 días en
calendario y 200 utilizados en hechos. El historial de cargas no se elimina.

La publicación SQL valida antes de borrar y usa una transacción con rollback.
La segunda ejecución reemplaza las filas y mantiene el total de 10,000.

En Power BI abrir `powerbi/Mantenimiento.pbip`, actualizar y mostrar la vista Modelo.
La fecha real de carga se almacena aparte, en UTC.'''),
        code('''verificacion = root / 'results/sqlserver/ultima_verificacion.json'
if verificacion.exists():
    evidencia = json.loads(verificacion.read_text(encoding='utf-8-sig'))
    print('Evidencia histórica: comprobar servidor, fecha e identificador antes de presentarla.')
    display(pd.Series(evidencia).to_frame('valor'))
else:
    print('Pendiente: ejecución y verificación reales de SQL Server/SSIS.')'''),
        md('''## 6. Conexión con los modelos
**Regresión:** estimar torque con tipo, temperaturas, velocidad y desgaste.
**Clasificación:** estimar Machine failure con tipo y las cinco mediciones.
**Agrupamiento:** formar perfiles con las cinco mediciones estandarizadas.

Fechas simuladas, identificadores e indicadores específicos de falla quedan fuera
de las entradas. Los notebooks previos conservan entrenamiento y evaluación;
esta migración no los reentrena.'''),
    ])
    notebook.metadata = {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                         'language_info': {'name': 'python', 'version': sys.version.split()[0]}}
    target = ROOT / 'notebooks/02_ETL_SQLServer.ipynb'
    nbf.write(notebook, target)
    print(target)


if __name__ == '__main__':
    generate()
