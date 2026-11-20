# Evidencias revisadas — 20 de noviembre de 2026

- `modelo_estrella.png`: captura aportada del esquema SQL Server, con `fact_operacion`, `dim_tipo`, `dim_estado` y `dim_tiempo`.
- `powerbi_totales.png`: captura aportada del reporte en Power BI Desktop: 10,000 observaciones, 339 fallas, 3.39 % de fallas y torque promedio de 39.99 Nm.
- Informe final: `../../reports/Informe_Final_Mantenimiento_Predictivo.docx`.

Los resultados de los tres modelos se conservan en `results/metricas_prueba.json`, `results/metricas_agrupamiento.json` y `results/perfiles_agrupamiento.csv`. No se entrenaron de nuevo para esta entrega. Las fechas del reporte son simuladas y no demuestran estacionalidad real.

La carga SQL se contrastó con el registro local `results/sqlserver/ultima_verificacion.json`, que permanece excluido de Git. La captura de Power BI respalda sus totales visibles; no acredita por sí sola la ejecución de SSIS. Se omite la evidencia de ejecución de SSIS por decisión del usuario, sin declarar el paquete como ejecutado correctamente.

La comprobación `scripts/verificar_entrega.py` acepta el modelo TMDL guardado por Desktop y valida referencias de tablas, campos y relaciones. Las tablas de fecha automáticas se distinguen de las cuatro tablas y tres relaciones de negocio. Esta comprobación estática no sustituye la apertura del reporte ni ejecuta SQL Server o SSIS.
