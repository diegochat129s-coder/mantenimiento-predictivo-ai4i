# Mantenimiento predictivo de maquinaria industrial

**Autor:** Diego Salinas Laguna. **Corte:** 27 de octubre de 2026.

Proyecto académico con AI4I 2020. Este paquete continúa la Actividad 0 y la Unidad I y reúne las evidencias de las Unidades II y III del calendario proporcionado. El informe principal está en `reports/Diego_Salinas_Unidades_II_III.pdf` y su versión editable en Word en la misma carpeta.

## Resultados finales

Se reservaron 2,000 registros exclusivamente para prueba. La regresión de torque obtuvo MAE **3.019 Nm**, RMSE **3.948 Nm** y R² **0.838**. El clasificador detectó **58 de 68 fallas**, omitió 10 y generó 56 falsas alarmas: recall **0.853**, precisión **0.509**, F1 **0.637**. El umbral **0.25** se eligió en validación, antes de consultar la prueba.

Los datos son sintéticos. Esto no demuestra predicción de fallas futuras con un tiempo de anticipación ni validez en equipos reales. Se preservaron 27 discrepancias entre la etiqueta general y las etiquetas de tipos de falla. No se inventaron correcciones.

## Contenido y evidencia

| Entrega | Evidencia |
|---|---|
| Diccionario | `data/processed/diccionario_datos.csv` |
| Calidad y limpieza | `results/auditoria.json`, `results/discrepancias_etiquetas.csv` |
| Exploración | `results/figures/`, estadísticas y correlaciones en `results/` |
| ETL ejecutable | `src/analisis.py` |
| Datos preparados | `data/processed/ai4i_limpio.csv` y particiones |
| Data Mart | `data/processed/mantenimiento.sqlite`, `sql/esquema.sql`, `sql/consultas.sql` |
| Modelos de regresión y clasificación | `models/` y código de entrenamiento |
| Optimización | `results/busqueda_*.csv`, `results/ajuste_umbral_validacion.csv` |
| Evaluación final | `results/metricas_prueba.json`, `results/predicciones_prueba.csv` |
| Notebook ejecutado | `notebooks/Unidades_II_III.ipynb` |
| Informe | `reports/Diego_Salinas_Unidades_II_III.pdf` y `.docx` |

## Ejecutar

Recomendado: Python 3.14, versión utilizada en la ejecución de referencia en un entorno virtual. Desde esta carpeta:

```console
python -m pip install -r requirements.txt
python src/analisis.py
```

Para generar el Word desde los resultados:

```console
python src/crear_informe.py
```

El PDF se exporta desde Word; no se regenera automáticamente con los comandos anteriores. El notebook puede abrirse en Jupyter o VS Code con un kernel que tenga las dependencias. Ejecutar sus celdas en orden reconstruye el análisis. Para usar Colab, subir y extraer el proyecto completo y conservar la estructura de carpetas; una celda inicial puede instalar `requirements.txt`. El notebook solo necesita localizar la carpeta `mantenimiento_predictivo` o ejecutarse dentro del proyecto.

## Diseño experimental

- Semilla 42, particiones 60% entrenamiento, 20% validación y 20% prueba; estratificadas por Machine failure y compartidas entre tareas.
- Entradas de clasificación: Type, Air temperature, Process temperature, Rotational speed, Torque y Tool wear.
- Objetivo de regresión: Torque; se excluye Torque de sus entradas.
- Identificadores y etiquetas de tipos de falla quedan fuera de ambos modelos; Machine failure también se excluye como entrada de regresión.
- Preparación mediante Pipeline: OneHotEncoder para Type y StandardScaler para variables numéricas, ajustados solo durante entrenamiento.
- Comparación de referencias, modelos lineales y bosques de 120 árboles. Búsqueda de cuatro configuraciones por bosque con validación cruzada de tres pliegues dentro de entrenamiento.
- Selección por RMSE para regresión y AP para clasificación en validación. Ajuste de umbral por F2, sin usar prueba.
- La prueba solo se usa para medir los modelos finales. Los modelos guardados siguen entrenados con las 6,000 filas iniciales, sin reentrenamiento posterior.

`models/clasificacion.joblib` contiene un diccionario con `pipeline` y `umbral`. Para clasificar se usa `pipeline.predict_proba(datos)[:, 1] >= umbral`; usar `pipeline.predict()` aplicaría el umbral predeterminado y no reproduciría el resultado reportado. `models/regresion.joblib` contiene el Pipeline de regresión. Abrir solamente modelos joblib de origen confiable.

## Data Mart y trazabilidad

Grano: una observación por UDI. Dimensiones de tipo de producto y estado general; tabla de hechos con medidas de operación y tipos de falla. No se inventan fechas ni identificadores de máquinas. El ETL reconstruye sus propias tablas y comprueba integridad referencial. Las consultas del Data Mart son descriptivas; no intervienen en la selección de modelos.

El CSV original permanece en `data/raw`. Su SHA-256 se registra en `results/auditoria.json`. Los resultados de comprobación están en `results/verificacion.json`. La exploración que orienta modelos usa entrenamiento; la revisión de calidad y las consultas de carga describen todo el archivo.

## Avance del Proyecto Integrador

La [guía de evidencias](docs/Avance_Proyecto_Integrador.md) reúne las ubicaciones de cada entrega.
El repositorio del proyecto es https://github.com/diegochat129s-coder/mantenimiento-predictivo-ai4i.

- Exploración AE1: [notebook](notebooks/SalinasLaguna_Diego_U2_AE1_Exploracion.ipynb) e [informe PDF](docs/SalinasLaguna_Diego_U2_AE1_Diagnostico.pdf).
- Agrupamiento: [notebook](notebooks/04_agrupamiento.ipynb), [modelo](models/agrupamiento.joblib) y [perfiles](results/perfiles_agrupamiento.csv). K-means produjo 3 grupos con silueta de prueba 0.268.
- Dashboard: descarga y abre [dashboard/index.html](dashboard/index.html) en el navegador. Incluye filtros por tipo de producto y conjunto de datos.

Para reproducir el flujo completo desde la raíz del repositorio:

```powershell
python -m pip install -r requirements.txt
python src/analisis.py
python src/agrupamiento.py
python src/generar_dashboard.py
python -m jupyter lab
```

En Jupyter, abre la carpeta `notebooks/`, selecciona Python 3 y ejecuta las celdas en orden.
Los datos procesados, gráficos y modelos se regeneran con los scripts. El CSV original permanece en `data/raw/`.

## Fuente y licencia de los datos

UCI Machine Learning Repository (2020), *AI4I 2020 Predictive Maintenance Dataset*. DOI: https://doi.org/10.24432/C5HS5C. Licencia **Creative Commons Attribution 4.0**, https://creativecommons.org/licenses/by/4.0/. El CSV original se redistribuye sin modificaciones, con atribución; las particiones y tablas derivadas se identifican en `data/processed`.

Documentación metodológica: https://scikit-learn.org/stable/common_pitfalls.html y https://scikit-learn.org/stable/modules/model_evaluation.html.
