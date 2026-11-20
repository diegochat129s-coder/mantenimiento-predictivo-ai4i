# Avance del Proyecto Integrador de Recursamiento

**Avance posterior a la instalación del 20 de noviembre:** se confirmó la conexión a `localhost` en SSMS, se configuró el proyecto y se generó y releyó `ssis/AI4I_Carga_Full.dtsx`. La carga SQL y la ejecución del paquete aún no están comprobadas: deben iniciarse desde la terminal normal del usuario, fuera del entorno restringido del asistente. Las instrucciones actuales están en la guía de instalación.

**Actualización del 20 de noviembre:** se preparó la migración a SQL Server con dimensión de tiempo simulada, carga FULL transaccional, generador de paquete SSIS y proyecto Power BI. La transformación Python está comprobada; la ejecución SQL/SSIS y la apertura de Power BI están pendientes de instalación/configuración. Ver [guía de presentación](GUIA_PRESENTACION.md) e [instrucciones de instalación](INSTALACION_SQLSERVER_SSIS_POWERBI.md). Los archivos y resultados de SQLite descritos abajo documentan la etapa anterior.

**Diego Salinas Laguna · Mantenimiento predictivo de maquinaria industrial**

| Evidencia | Ubicación |
|---|---|
| Dataset original | [data/raw/ai4i2020.csv](../data/raw/ai4i2020.csv) |
| Exploración inicial | [Notebook Unidad II](../notebooks/SalinasLaguna_Diego_U2_AE1_Exploracion.ipynb) y [PDF de diagnóstico](SalinasLaguna_Diego_U2_AE1_Diagnostico.pdf) |
| Dataset procesado y particiones | [data/processed](../data/processed) |
| Exploración, ETL y modelos supervisados | [Notebook de Unidades II y III](../notebooks/Unidades_II_III.ipynb) y [script de análisis](../src/analisis.py) |
| Esquema y consulta SQL | [sql](../sql) |
| Data Mart | [mantenimiento.sqlite](../data/processed/mantenimiento.sqlite) |
| Informe de Unidades II y III | [PDF](../reports/Diego_Salinas_Unidades_II_III.pdf) y [Word](../reports/Diego_Salinas_Unidades_II_III.docx) |
| Modelos de regresión, clasificación y agrupamiento | [models](../models) |
| Análisis no supervisado | [Notebook de agrupamiento](../notebooks/04_agrupamiento.ipynb) y [resultados](../results/perfiles_agrupamiento.csv) |
| Dashboard | [dashboard/index.html](../dashboard/index.html). Descargar y abrir en un navegador. |
| Guía de ejecución | [README](../README.md) |

El CSV contiene 10,000 registros sintéticos. La auditoría encontró cero valores faltantes, cero filas completamente duplicadas y 27 discrepancias entre la etiqueta general de falla y sus indicadores específicos. El Data Mart de SQLite contiene una fila de hechos por observación.

En 2,000 registros de prueba, el modelo de regresión tuvo un error absoluto medio de aproximadamente 3.02 Nm. El clasificador detectó 58 de 68 fallas y produjo 56 falsas alarmas.

Para el agrupamiento se probaron entre dos y seis grupos, usando cinco mediciones de operación. Con la mayor silueta en validación se eligieron tres grupos. La silueta de prueba de 0.268 indica una separación limitada. El grupo 3 tuvo 206 fallas entre 3,894 registros (5.29%). Esa proporción describe el conjunto sintético y puede servir para explorar diferencias entre perfiles.

En la revisión, se puede ejecutar el notebook de exploración, mostrar la tabla de calidad, abrir el Data Mart y cambiar los filtros de tipo de producto y conjunto en el dashboard. Para cada corte se pueden enlazar los commits que ya estén publicados en el repositorio y detallar qué se comprobó desde el corte anterior.
