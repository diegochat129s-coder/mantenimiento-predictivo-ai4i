"""Informe PDF de la arquitectura propuesta y su estado real de verificación."""
from pathlib import Path
import hashlib
import textwrap

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
BLUE = '#1e3a8a'
INK = '#172033'


def page(title, number):
    fig = plt.figure(figsize=(8.27, 11.69), facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis('off')
    ax.text(.08, .94, 'MANTENIMIENTO PREDICTIVO', color=BLUE, fontsize=10, weight='bold')
    ax.text(.08, .89, title, color=INK, fontsize=20, weight='bold', va='top')
    ax.plot([.08, .92], [.84, .84], color='#bfdbfe', linewidth=2)
    ax.text(.08, .04, 'Diego Salinas Laguna · AI4I 2020 · 20 noviembre 2026', color='#64748b', fontsize=8)
    ax.text(.92, .04, str(number), ha='right', color='#64748b', fontsize=8)
    return fig, ax


def paragraph(ax, y, text, width=90, size=10):
    wrapped = '\n'.join(textwrap.wrap(text, width=width))
    ax.text(.08, y, wrapped, fontsize=size, color=INK, va='top', linespacing=1.5)
    return y - len(wrapped.splitlines()) * .020 - .025


def box(ax, x, y, w, h, title, lines):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.008',
                             facecolor='#eff6ff', edgecolor='#93c5fd'))
    ax.text(x + .018, y + h - .028, title, color=BLUE, fontsize=10, weight='bold', va='top')
    ax.text(x + .018, y + h - .060, '\n'.join(lines), color=INK, fontsize=9, va='top', linespacing=1.4)


def generate():
    raw = ROOT / 'data/raw/ai4i2020.csv'
    df = pd.read_csv(raw)
    output = ROOT / 'docs/Informe_SQLServer_SSIS_PowerBI.pdf'
    with PdfPages(output) as pdf:
        fig, ax = page('Modelo estrella y Data Mart', 1)
        y = paragraph(ax, .80, 'Objetivo: organizar las observaciones de operación industrial para explorar condiciones, describir fallas y facilitar su consulta en Power BI.')
        paragraph(ax, y, 'Estado: transformación Python ejecutada, pruebas aprobadas y estructura Power BI validada. El paquete SSIS ya se generó y releyó con cinco tareas. La carga SQL, la ejecución del paquete y la apertura del informe en Power BI siguen pendientes. La conexión local está configurada para localhost.')
        box(ax, .34, .48, .32, .12, 'dm.dim_tiempo', ['tiempo_id (PK), fecha', 'año, mes, día, simulación'])
        box(ax, .08, .25, .23, .14, 'dm.dim_tipo', ['tipo_id (PK)', 'L, M, H / calidad'])
        box(ax, .35, .23, .30, .18, 'dm.fact_operacion', ['udi (PK), tres claves (FK)', 'temperaturas, velocidad', 'torque, desgaste y fallas'])
        box(ax, .69, .25, .23, .14, 'dm.dim_estado', ['estado_id (PK)', 'Sin falla / Con falla'])
        for start, end in [((.5, .48), (.5, .41)), ((.31, .32), (.35, .32)), ((.69, .32), (.65, .32))]:
            ax.annotate('', xy=end, xytext=start, arrowprops={'arrowstyle': '->', 'color': BLUE, 'lw': 1.7})
        paragraph(ax, .17, 'Grano: una observación por UDI. Cada dimensión tiene una relación de uno a muchos con la tabla central. UDI no identifica una máquina seguida en el tiempo.')
        pdf.savefig(fig); plt.close(fig)

        fig, ax = page('ETL: carga FULL automática', 2)
        tasks = [
            ('1. Preparar objetos SQL', 'Crear base, tablas y procedimiento si corresponde.'),
            ('2. Extraer y transformar', 'Leer CSV, validar tipos y generar fechas simuladas.'),
            ('3. Cargar staging', 'Enviar 10,000 filas con SqlBulkCopy e identificar la ejecución.'),
            ('4. Publicar FULL', 'Validar, reemplazar dimensiones y hechos, registrar auditoría.'),
            ('5. Verificar', 'Comprobar filas, fallas, calendario e identificador de carga.'),
        ]
        for i, (title, detail) in enumerate(tasks):
            y = .72 - i * .113
            box(ax, .10, y, .80, .08, title, [detail])
            if i < 4:
                ax.annotate('', xy=(.5, y - .030), xytext=(.5, y - .004),
                            arrowprops={'arrowstyle': '->', 'color': BLUE})
        paragraph(ax, .20, 'SSIS coordina cinco tareas Execute Process. Python realiza la preparación y PowerShell/SQL realizan la carga. No se utilizan componentes de Data Flow en esta implementación.')
        paragraph(ax, .12, 'FULL reemplaza los datos en cada ejecución sin borrado manual. La publicación usa una transacción y rollback; conserva el historial de cargas. Automático al ejecutar no significa programado por horario.', size=9)
        pdf.savefig(fig); plt.close(fig)

        fig, ax = page('Fechas y calidad de los datos', 3)
        y = paragraph(ax, .80, 'AI4I no incluye fechas originales. Se incorpora un calendario simulado exclusivamente para la práctica y para demostrar filtros temporales. La fecha real de carga se registra aparte en UTC.')
        y = paragraph(ax, y, 'Regla: 1 de enero de 2026 + parte entera de ((UDI - 1) / 50) días. Las fechas no cambian entre recargas.')
        rows = [['1 al 50', '01/01/2026'], ['51 al 100', '02/01/2026'], ['9,951 al 10,000', '19/07/2026']]
        table = ax.table(cellText=rows, colLabels=['UDI', 'Fecha simulada'], bbox=[.08, .51, .84, .16], cellLoc='center')
        table.auto_set_font_size(False); table.set_fontsize(10)
        for (r, _), cell in table.get_celld().items():
            cell.set_edgecolor('#cbd5e1')
            if r == 0:
                cell.set_facecolor(BLUE); cell.set_text_props(color='white', weight='bold')
        y = paragraph(ax, .47, 'El calendario tiene 365 días. Las 10,000 observaciones ocupan 200 días, con 50 observaciones por día. Las diferencias entre meses proceden de esta asignación; no prueban estacionalidad real.')
        disagreements = df['Machine failure'].ne(df[['TWF','HDF','PWF','OSF','RNF']].max(axis=1)).sum()
        y = paragraph(ax, y, f'Calidad observada: {len(df):,} filas; {int(df.isna().sum().sum())} nulos; {int(df.duplicated().sum())} filas duplicadas; {int(df["Machine failure"].sum())} fallas; {int(disagreements)} discrepancias entre etiquetas general y específicas. Las discrepancias se conservan y reportan.')
        y = paragraph(ax, y, 'El original permanece en data/raw/ai4i2020.csv. Los derivados con fecha se guardan en data/processed. Cada carga prepara un manifiesto con identificador, conteos y huellas SHA-256.')
        ax.text(.08, .12, 'SHA-256 del original:', fontsize=9, color=INK)
        ax.text(.08, .095, hashlib.sha256(raw.read_bytes()).hexdigest(), fontsize=7.5, color=BLUE)
        pdf.savefig(fig); plt.close(fig)

        fig, ax = page('Demostración y análisis', 4)
        y = .80
        for text in [
            '1. Mostrar el CSV original y el notebook de exploración: variables, nulos, duplicados, medias, medianas y un boxplot.',
            '2. Ejecutar notebooks/02_ETL_SQLServer.ipynb para mostrar la transformación y las fechas simuladas.',
            '3. Generar el paquete con ssis/Crear_Paquete.ps1 y ejecutarlo en Visual Studio con Integration Services. Conservar evidencia de las cinco tareas en verde.',
            '4. Consultar SQL Server y repetir el FULL: deben mantenerse 10,000 hechos, 339 fallas y un calendario de 365 días; la auditoría debe aumentar una carga.',
            '5. Abrir powerbi/Mantenimiento.pbip, actualizar datos, mostrar las relaciones y probar los filtros de mes, tipo y estado.',
        ]:
            y = paragraph(ax, y, text)
        y = paragraph(ax, y, 'Regresión: estimar torque con tipo, temperaturas, velocidad y desgaste. Clasificación: estimar la falla general con tipo y cinco mediciones. Agrupamiento: reunir perfiles similares usando las cinco mediciones estandarizadas.')
        y = paragraph(ax, y, 'Los modelos previos se conservan. Las fechas simuladas y los identificadores no se agregan como entradas. Los indicadores específicos de falla tampoco se usan como predictores.')
        paragraph(ax, y, 'Guías: docs/GUIA_PRESENTACION.md y docs/INSTALACION_SQLSERVER_SSIS_POWERBI.md. Fuente del dataset: UCI, AI4I 2020, DOI 10.24432/C5HS5C, licencia CC BY 4.0.', size=9)
        pdf.savefig(fig); plt.close(fig)
    print(output)


if __name__ == '__main__':
    generate()
