"""Genera el informe académico a partir de resultados ejecutados."""
from pathlib import Path
import json
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'
metrics=json.loads((R/'metricas_prueba.json').read_text(encoding='utf-8'))
a=json.loads((R/'auditoria.json').read_text(encoding='utf-8'))
d=Document(); s=d.sections[0]
s.page_width=Inches(8.5); s.page_height=Inches(11)
s.top_margin=s.bottom_margin=Inches(.7); s.left_margin=s.right_margin=Inches(.8)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
 st=d.styles[name]; st.font.name='Calibri'; st.font.color.rgb=RGBColor(0,0,0)
d.styles['Normal'].font.size=Pt(11)
d.styles['Normal'].paragraph_format.space_after=Pt(7)
d.styles['Normal'].paragraph_format.line_spacing=1.1
d.styles['Title'].font.size=Pt(25)
d.styles['Heading 1'].font.size=Pt(18)
d.styles['Heading 2'].font.size=Pt(13)
for st in d.styles:
 for border in st.element.xpath('.//w:pBdr'):
  border.getparent().remove(border)
footer=s.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('Diego Salinas Laguna | ')
field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); footer._p.append(field)
def p(text):return d.add_paragraph(text)
def h(text):return d.add_heading(text,2)
def page(title):
 heading=d.add_heading(title,1)
 heading.paragraph_format.page_break_before=True
def picture(name,width=5.8):d.add_picture(str(R/'figures'/name),width=Inches(width))
def table(headers,rows,widths=None):
 t=d.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
 if widths:
  for col,width in zip(t.columns,widths):col.width=Inches(width)
 for c,txt in zip(t.rows[0].cells,headers):c.text=str(txt)
 for row in rows:
  for c,txt in zip(t.add_row().cells,row):c.text=str(txt)
 for i,row in enumerate(t.rows):
  for j,c in enumerate(row.cells):
   if widths:c.width=Inches(widths[j])
   c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   pr=c._tc.get_or_add_tcPr()
   sh=OxmlElement('w:shd'); sh.set(qn('w:fill'),'244B65' if i==0 else ('F1F5F7' if i%2 else 'FFFFFF')); pr.append(sh)
   borders=OxmlElement('w:tcBorders')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge); e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
   pr.append(borders)
   mar=OxmlElement('w:tcMar')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:w'),'90');e.set(qn('w:type'),'dxa');mar.append(e)
   pr.append(mar)
   for par in c.paragraphs:
    par.paragraph_format.space_after=Pt(1);par.paragraph_format.line_spacing=1
    for run in par.runs:
     run.font.size=Pt(10)
     if i==0:run.bold=True;run.font.color.rgb=RGBColor(255,255,255)
  trpr=row._tr.get_or_add_trPr(); trpr.append(OxmlElement('w:cantSplit'))
 repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
 d.add_paragraph().paragraph_format.space_after=Pt(0)
 return t

d.add_heading('Mantenimiento predictivo de maquinaria industrial',0)
p('Unidades II y III\nPreparación de datos y análisis supervisado')
p('Diego Salinas Laguna\nUniversidad Tecnológica de Tula-Tepeji\nIngeniería en Desarrollo y Gestión de Software\n27 de octubre de 2026')
h('Resumen del trabajo')
p('En este trabajo doy continuidad a la planeación de la Unidad I con el dataset AI4I 2020. Preparé los datos, construí un Data Mart y comparé modelos para estimar el torque y reconocer registros con falla. El propósito es comprobar qué resultados se pueden obtener y explicar sus límites con evidencia reproducible.')
p(f'El archivo contiene 10,000 registros y 14 columnas. No encontré valores faltantes ni filas duplicadas. De los registros, 339 tienen la etiqueta de falla. En la prueba final, el modelo de clasificación detectó 58 de 68 fallas y produjo 56 falsas alarmas. El modelo de regresión obtuvo un error absoluto promedio de {metrics["regresion"]["MAE"]:.2f} Nm.')
p('Los datos son sintéticos. Los resultados representan reconocimiento de condiciones asociadas con fallas en este conjunto, sin demostrar anticipación temporal ni funcionamiento en una fábrica real.')
h('Contenido')
table(['Apartado','Evidencia'],[['Unidad II','Diccionario, calidad, exploración, ETL y Data Mart'],['Unidad III','Particiones, modelos, optimización y evaluación'],['Reproducibilidad','Código, notebook, métricas, predicciones y modelos guardados']],[1.5,5.3])

page('Unidad II Comprensión y diccionario de datos')
p('La fuente es el UCI Machine Learning Repository. El archivo ai4i2020.csv contiene observaciones de operación industrial simuladas. Cada fila es un registro, no una máquina identificada ni un historial de mantenimiento. La variable Type expresa variantes de calidad del producto: L baja, M media y H alta.')
dic=pd.read_csv(ROOT/'data/processed/diccionario_datos.csv')
shorttypes=['Entero','Texto','Categoría','Decimal','Decimal','Entero','Decimal','Entero']+['Binaria']*6
rows=[[row.variable,shorttypes[i],row.unidad,row.descripcion] for i,row in enumerate(dic.itertuples())]
table(['Variable','Tipo','Unidad','Significado'],rows,[2.05,.75,.55,3.45])
p('Para clasificación se usan las seis variables de operación, incluido Torque. Para regresión, Torque es el objetivo y se retira de las entradas. UDI y Product ID se excluyen de ambos modelos; Machine failure y los cinco tipos de falla tampoco se usan como predictores del torque.')

page('Unidad II Calidad y decisiones de limpieza')
table(['Revisión del archivo completo','Resultado'],[['Registros y columnas','10,000 y 14'],['Valores faltantes','0'],['Filas duplicadas completas','0'],['UDI duplicados','0'],['Combinaciones repetidas de los seis predictores','0'],['Sin falla y con falla','9,661 y 339'],['Discrepancias entre falla general y tipos de falla','27']],[4.8,2])
p('Validé el esquema, los identificadores, las categorías L/M/H, las etiquetas binarias y los rangos básicos. Temperaturas, velocidad y torque son positivos; el desgaste no es negativo. No fue necesario imputar valores ni eliminar registros. La versión procesada conserva las 10,000 observaciones y sus etiquetas originales.')
h('Valores extremos')
p('La regla de 1.5 veces el rango intercuartílico marca 418 valores de velocidad y 69 de torque como extremos en el archivo completo. Es una revisión descriptiva de calidad, no una regla de eliminación. Los valores extremos pueden representar condiciones relevantes para una falla, por lo que se conservaron. No se aplicó recorte ni una transformación aprendida del conjunto completo.')
h('Discrepancias entre etiquetas')
p('Comparé Machine failure con el máximo de TWF, HDF, PWF, OSF y RNF. En 27 filas no coinciden. Guardé esas observaciones en discrepancias_etiquetas.csv para mantener trazabilidad. No cambié sus respuestas porque no hay evidencia suficiente para decidir cuál etiqueta es correcta. La evaluación utiliza Machine failure tal como aparece en el archivo original.')
h('Prevención de información indebida')
p('Las columnas de tipos de falla se conservan para auditoría y consulta del Data Mart, pero quedan excluidas de los modelos. Usarlas para predecir la falla general daría información demasiado cercana a la respuesta. La codificación de Type y el escalado se ajustan dentro de cada entrenamiento mediante un Pipeline.')

page('Unidad II Exploración de las variables')
p('La exploración que puede orientar el modelado se realizó sobre los 6,000 registros de entrenamiento. En ellos hay 203 fallas y 5,797 casos sin falla. Esta diferencia explica por qué un porcentaje alto de aciertos puede ocultar un modelo que no detecta ninguna falla.')
picture('clases.png',5.6)
picture('distribuciones.png',6.15)
p('Las distribuciones permiten revisar escala y dispersión. Las temperaturas se expresan en kelvin, la velocidad en rpm, el torque en Nm y el desgaste en minutos. Estas unidades se mantienen en los archivos procesados.')

page('Unidad II Relaciones observadas y proceso ETL')
picture('correlaciones.png',5.4)
corr=pd.read_csv(R/'correlacion_entrenamiento.csv',index_col=0)
p(f'En entrenamiento, velocidad y torque tienen una correlación de {corr.loc["Rotational speed [rpm]","Torque [Nm]"]:.2f}. Esta relación ayuda a justificar la estimación del torque. Las temperaturas también están relacionadas entre sí. Una correlación describe asociación; no demuestra causalidad ni determina por sí sola qué variable será más útil para un modelo no lineal.')
h('Extracción')
p('Se toma el CSV original descargado de UCI. Se conserva sin cambios en data/raw y se registra su huella SHA-256 en auditoria.json para identificar exactamente la entrada utilizada.')
h('Transformación')
p('Se comprueban columnas, tipos y reglas de calidad. Se generan el diccionario, la auditoría y las particiones. La limpieza no elimina filas al no encontrar faltantes ni duplicados. OneHotEncoder transforma Type en indicadores y StandardScaler estandariza las variables numéricas dentro del Pipeline. Los árboles no necesitan escalado, pero lo admiten y así se mantiene una preparación común.')
h('Carga')
p('Se escriben los CSV procesados y se cargan las dimensiones y la tabla de hechos en SQLite. Se verifican las 10,000 filas de hechos y las claves foráneas. El proceso puede ejecutarse de nuevo y reconstruye las tablas sin duplicar registros.')

page('Unidad II Data Mart de mantenimiento')
p('El Data Mart usa un esquema en estrella con granularidad de una observación por fila. La tabla fact_operacion conserva las medidas de operación y los indicadores de falla. Se relaciona con dim_tipo y dim_estado mediante claves foráneas. Product ID se conserva como identificador descriptivo en la tabla de hechos.')
table(['Tabla','Clave','Contenido'],[['dim_tipo','tipo_id','Tres variantes de calidad L, M y H'],['dim_estado','estado_id','Estados sin falla y con falla'],['fact_operacion','udi','Producto, claves de dimensiones, cinco medidas y cinco tipos de falla']],[1.5,1,4.3])
p('Relaciones: dim_tipo.tipo_id → fact_operacion.tipo_id; dim_estado.estado_id → fact_operacion.estado_id. Cada fila de hechos tiene un tipo y un estado. Las dimensiones pueden relacionarse con muchas observaciones.')
p('No se creó una dimensión de fecha ni una de máquina: el CSV no proporciona fecha real ni identificador de máquina. Interpretar UDI como una fecha o como una máquina introduciría información que no existe en la fuente.')
h('Consulta de comprobación del archivo completo')
mart=pd.read_csv(R/'resumen_datamart.csv')
table(['Tipo','Registros','Fallas','Fallas %','Torque medio'],[[r.tipo,r.registros,r.fallas,f'{r.porcentaje_fallas:.2f}',f'{r.torque_medio:.2f}'] for r in mart.itertuples()],[.6,1.2,1,1.2,1.8])
p('Esta consulta resume el archivo completo para comprobar la carga y facilitar consultas administrativas. No se utiliza para escoger modelos ni ajustar sus parámetros. Los scripts esquema.sql y consultas.sql documentan la estructura y la consulta realizada.')
h('Archivos de la Unidad II')
p('data/processed contiene el CSV limpio, el diccionario, las tres particiones, el mapa de UDI a partición y mantenimiento.sqlite. results contiene la auditoría, estadísticas, discrepancias y gráficas. Los archivos de entrada se conservan separados de los resultados.')

page('Unidad III Diseño experimental y modelos')
p('Las dos tareas siguen los objetivos de la Unidad I: estimar Torque [Nm] con las otras cinco variables y clasificar Machine failure con las seis variables. La semilla es 42. Se hizo una separación aleatoria estratificada por falla para conservar la proporción de clases, compartida por ambas tareas.')
table(['Partición','Registros','Fallas','Uso'],[['Entrenamiento','6,000','203','Ajustar modelos y buscar parámetros'],['Validación','2,000','68','Elegir modelo y umbral'],['Prueba','2,000','68','Evaluación final sin reajuste']],[1.35,.9,.7,3.85])
p('Las particiones no comparten UDI. El conjunto de prueba permanece fuera de la selección. No se reentrenó con validación después de ajustar el umbral, para conservar el mismo modelo con el que se eligió dicho umbral. La separación aleatoria mide generalización dentro de esta distribución sintética; no constituye una validación temporal para fallas futuras.')
h('Modelos comparados')
table(['Tarea','Referencia','Modelos aprendidos'],[['Regresión','Promedio de entrenamiento','Regresión lineal y bosque aleatorio'],['Clasificación','Siempre sin falla','Regresión logística y bosque aleatorio']],[1.2,2,3.6])
p('La regresión logística y el bosque clasificador usan class_weight="balanced" para dar más peso a la clase minoritaria. No se generaron datos artificiales ni se alteró el conjunto de prueba. Los bosques usan 120 árboles y semilla 42.')
h('Optimización y criterio de selección')
p('Se probaron cuatro combinaciones por bosque: profundidad máxima 8 o sin límite, y tamaño mínimo de hoja 1 o 4. La búsqueda usa tres pliegues en entrenamiento; los de clasificación son estratificados. El criterio es menor RMSE para regresión y mayor average precision (AP) para clasificación. Después se comparan las familias de modelos en validación.')
p('El bosque regresor seleccionado usa profundidad 8 y hoja mínima 1; el clasificador usa profundidad sin límite y hoja mínima 1. La comparación detallada de las búsquedas está en los archivos busqueda_regresion.csv y busqueda_clasificacion.csv.')

page('Unidad III Resultados de regresión')
p('La regresión estima el torque a partir de Type, las dos temperaturas, velocidad y desgaste. La referencia predice el promedio de torque aprendido en entrenamiento. MAE representa el tamaño medio del error; RMSE penaliza más los errores grandes; R² compara la variación explicada con una referencia constante.')
rt=pd.read_csv(R/'comparacion_regresion_validacion.csv')
table(['Modelo en validación','MAE Nm','RMSE Nm','R²'],[[r.modelo,f'{r.MAE:.3f}',f'{r.RMSE:.3f}',f'{r.R2:.3f}'] for r in rt.itertuples()],[2.6,1.4,1.4,1.4])
p('El bosque obtuvo el menor RMSE de validación y se eligió antes de evaluar la prueba. En la búsqueda interna su mejor RMSE medio fue 3.939 Nm. La regresión lineal mejora frente al promedio, pero no alcanza al bosque en esta partición.')
rr=metrics['regresion']
table(['Modelo final en prueba','MAE Nm','RMSE Nm','R²'],[['Bosque aleatorio',f'{rr["MAE"]:.3f}',f'{rr["RMSE"]:.3f}',f'{rr["R2"]:.3f}']],[2.6,1.4,1.4,1.4])
picture('regresion.png',5.35)
p('Los puntos cercanos a la diagonal representan estimaciones próximas al valor real. El error no desaparece, especialmente en algunas observaciones extremas. R² no es un porcentaje de predicciones correctas ni demuestra que el modelo sirva para cualquier máquina.')

page('Unidad III Clasificación y ajuste del umbral')
p('La clase positiva es falla. Precision indica cuántas alertas corresponden a fallas reales; recall indica cuántas fallas se detectan. F1 equilibra ambas medidas. AP resume la relación entre precisión y recall a distintos umbrales; aquí no se presenta como el área trapezoidal de la curva.')
ct=pd.read_csv(R/'comparacion_clasificacion_validacion.csv')
table(['Modelo en validación','Precision','Recall','F1','AP'],[[r.modelo,f'{r.precision:.3f}',f'{r.recall:.3f}',f'{r.F1:.3f}',f'{r.AP:.3f}'] for r in ct.itertuples()],[2.4,1.1,1.1,1.1,1.1])
p('La tabla usa umbral 0.50. La referencia siempre sin falla logra 96.6% de exactitud en validación, pero su recall es cero. El bosque se seleccionó por su AP de validación, superior a la logística. Su AP media en la búsqueda interna fue 0.672.')
th=pd.read_csv(R/'ajuste_umbral_validacion.csv'); chosen=th.iloc[(th.umbral-.25).abs().argmin()]
p(f'Con el bosque seleccionado se probaron 33 umbrales entre 0.05 y 0.85, en pasos de 0.025. Se eligió 0.25 por el mayor F2 de validación; los empates favorecen precisión y luego umbral mayor. F2 da más peso al recall. En validación, este umbral obtuvo precision {chosen.precision:.3f}, recall {chosen.recall:.3f} y F2 {chosen.F2:.3f}. Se trata de una preferencia académica por detectar fallas, no de un costo industrial validado.')
cc=metrics['clasificacion']
table(['Métrica final en prueba','Resultado'],[['Precision',f'{cc["precision"]:.3f}'],['Recall',f'{cc["recall"]:.3f}'],['F1 y F2',f'{cc["F1"]:.3f} y {cc["F2"]:.3f}'],['AP y ROC AUC',f'{cc["AP"]:.3f} y {cc["ROC_AUC"]:.3f}'],['Exactitud',f'{100*cc["accuracy"]:.2f}%']],[4.4,2.4])
p('La exactitud final por sí sola aporta poco: siempre predecir sin falla obtendría 96.6% en esta prueba. La utilidad del modelo está en detectar fallas, con el costo de generar alertas incorrectas. El puntaje del bosque no se ha calibrado como probabilidad para decisiones industriales.')

page('Unidad III Interpretación de los errores')
picture('matriz_confusion.png',3.3)
p('En prueba se detectaron 58 fallas y se omitieron 10. De los registros sin falla, 1,876 se clasificaron correctamente y 56 produjeron una falsa alarma. Hubo 114 alertas en total; alrededor de la mitad correspondió a una falla real. El modelo debe entenderse como apoyo a una revisión, no como una orden automática de detener maquinaria.')
picture('precision_recall.png',3.4)
p('La curva muestra el intercambio entre detectar más fallas y mantener alertas confiables. No se cambió el umbral después de observar la prueba. Las predicciones individuales, con UDI, respuesta real y estimación, están disponibles en predicciones_prueba.csv.')

page('Conclusiones y alcance de los resultados')
imp=pd.read_csv(R/'importancia_validacion.csv')
h('Qué aportan las variables')
p('Como diagnóstico adicional calculé importancia por permutación sobre validación, con cinco repeticiones y AP como medida. Se altera una entrada a la vez y se observa cuánto baja el desempeño. Las variables relacionadas pueden compartir información, por lo que esta medida no equivale a causalidad.')
table(['Variable','Reducción media de AP'],[[r.variable,f'{r.reduccion_AP_media:.4f}'] for r in imp.itertuples()],[4.8,2])
h('Conclusiones')
p('La preparación produjo datos trazables y un Data Mart consultable. No hubo que inventar valores ni eliminar observaciones, pero sí documentar el desbalance y las discrepancias entre etiquetas. El bosque fue la mejor familia de las comparadas para ambas tareas bajo los criterios fijados.')
p('La estimación de torque tuvo un MAE de 3.02 Nm y R² de 0.838. En clasificación, el recall de 0.853 permite reconocer buena parte de las fallas de prueba, pero las 56 falsas alarmas muestran un costo importante. Una aplicación posterior tendría que fijar costos de error, revisar la calibración y validar con observaciones reales independientes.')
h('Limitaciones')
p('Los datos son sintéticos y solo hay 68 fallas en la prueba. Una sola partición no mide toda la variación posible. Las 27 discrepancias de etiquetas introducen incertidumbre. No hay historial de mantenimiento, costos ni marcas de tiempo reales para demostrar anticipación. No se estimó vida útil restante y el agrupamiento queda fuera de estas unidades supervisadas.')

page('Reproducibilidad y referencias')
h('Cómo repetir el análisis')
p('Con Python 3.12, instalar las versiones de requirements.txt y ejecutar python src/analisis.py desde la carpeta del proyecto. El script lee el CSV original, reconstruye los datos procesados y SQLite, entrena modelos y vuelve a generar métricas y gráficas. El notebook ofrece una ejecución por etapas del mismo código.')
p('Los modelos quedan en models. Para clasificación se guarda también el umbral 0.25. La carga de ambos modelos se comprobó y se verificó que reproduzcan las predicciones. Solo deben abrirse archivos joblib de origen confiable. verificacion.json registra las comprobaciones realizadas.')
h('Calendario de entrega')
table(['Hito del calendario proporcionado','Fecha'],[['Unidad II Preparación de datos','16 de octubre de 2026'],['Revisión de Unidad III','23 de octubre de 2026'],['Unidad III Análisis supervisado','30 de octubre de 2026']],[4.8,2])
p('Este informe reúne las evidencias de preparación y análisis supervisado con fecha de elaboración del 27 de octubre de 2026. El cronograma preliminar de la Unidad I se sustituye, para estas etapas, por las fechas de entrega anteriores.')
h('Referencias')
p('UCI Machine Learning Repository. (2020). AI4I 2020 Predictive Maintenance Dataset. https://doi.org/10.24432/C5HS5C. Licencia CC BY 4.0. Archivo original conservado sin modificaciones.')
p('Matzka, S. (2020). Explainable Artificial Intelligence for Predictive Maintenance Applications. AI4I, 69-74. https://doi.org/10.1109/AI4I49448.2020.00023. Referencia del dataset indicada por UCI.')
p('scikit-learn. (2026). Common pitfalls and recommended practices. https://scikit-learn.org/stable/common_pitfalls.html. Consulta: 27 de octubre de 2026.')
p('scikit-learn. (2026). Metrics and scoring: quantifying the quality of predictions. https://scikit-learn.org/stable/modules/model_evaluation.html. Consulta: 27 de octubre de 2026.')
p('Antecedentes: Actividad 0 y planeación de Unidad I de Diego Salinas Laguna; calendario de entregas proporcionado para el proyecto.')
out=ROOT/'reports/Diego_Salinas_Unidades_II_III.docx';d.save(out);print(out)
