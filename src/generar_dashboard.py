"""Genera el panel local a partir de las evidencias del proyecto."""
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
results = ROOT / 'results'
data = pd.read_csv(ROOT / 'data/processed/ai4i_limpio.csv')
groups = pd.read_csv(results / 'asignacion_agrupamiento.csv')
data = data.merge(groups, on='UDI', validate='one_to_one')
summary = data.groupby(['Type', 'grupo', 'particion']).agg(
    n=('UDI', 'size'),
    fallas=('Machine failure', 'sum'),
    torque=('Torque [Nm]', 'sum'),
).reset_index()
payload = {
    'rows': summary.to_dict('records'),
    'supervisado': json.loads((results / 'metricas_prueba.json').read_text(encoding='utf8')),
    'agrupamiento': json.loads((results / 'metricas_agrupamiento.json').read_text(encoding='utf8')),
}
folder = ROOT / 'dashboard'
template = (folder / 'plantilla.html').read_text(encoding='utf8')
(folder / 'index.html').write_text(template.replace('/*DATOS_AI4I*/null', json.dumps(payload)), encoding='utf8')
print(folder / 'index.html')
