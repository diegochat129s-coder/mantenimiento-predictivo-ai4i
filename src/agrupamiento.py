"""Entrena K-means con las mediciones de AI4I y genera evidencias."""
from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FEATURES = [
    'Air temperature [K]',
    'Process temperature [K]',
    'Rotational speed [rpm]',
    'Torque [Nm]',
    'Tool wear [min]',
]


def ejecutar(root=ROOT):
    processed = root / 'data/processed'
    results = root / 'results'
    models = root / 'models'
    for directory in (results, models):
        directory.mkdir(exist_ok=True)
    train = pd.read_csv(processed / 'entrenamiento.csv')
    validation = pd.read_csv(processed / 'validacion.csv')
    x_train = train[FEATURES]
    x_validation = validation[FEATURES]
    selected = None
    comparisons = []
    best_score = -1.0
    for k in range(2, 7):
        candidate = make_pipeline(StandardScaler(), KMeans(n_clusters=k, n_init=20, random_state=42))
        candidate.fit(x_train)
        normalized = candidate.named_steps['standardscaler'].transform(x_validation)
        labels = candidate.predict(x_validation)
        score = float(silhouette_score(normalized, labels))
        comparisons.append({'k': k, 'silueta_validacion': score})
        if score > best_score:
            best_score, selected = score, candidate

    data = pd.read_csv(processed / 'ai4i_limpio.csv')
    splits = pd.read_csv(processed / 'particiones.csv')
    assigned = data.merge(splits, on='UDI', validate='one_to_one')
    if len(assigned) != len(data) or len(assigned) != len(splits):
        raise ValueError('Las particiones no cubren el dataset completo.')
    assigned['grupo'] = selected.predict(assigned[FEATURES]) + 1
    profiles = assigned.groupby('grupo').agg(
        registros=('UDI', 'size'),
        fallas=('Machine failure', 'sum'),
        **{name: (name, 'mean') for name in FEATURES},
    ).reset_index()
    profiles['porcentaje_fallas'] = profiles['fallas'] / profiles['registros'] * 100
    test = assigned.loc[assigned['particion'].eq('prueba')]
    transformed_test = selected.named_steps['standardscaler'].transform(test[FEATURES])
    k = selected.named_steps['kmeans'].n_clusters
    metrics = {
        'k_elegido': k,
        'silueta_validacion': best_score,
        'silueta_prueba': float(silhouette_score(transformed_test, test['grupo'])),
        'variables': FEATURES,
        'registros_entrenamiento': len(train),
        'registros_validacion': len(validation),
        'registros_prueba': len(test),
        'semilla': 42,
    }
    pd.DataFrame(comparisons).to_csv(results / 'comparacion_agrupamiento.csv', index=False)
    profiles.to_csv(results / 'perfiles_agrupamiento.csv', index=False)
    assigned[['UDI', 'particion', 'grupo']].to_csv(results / 'asignacion_agrupamiento.csv', index=False)
    (results / 'metricas_agrupamiento.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    joblib.dump(selected, models / 'agrupamiento.joblib')
    return metrics


if __name__ == '__main__':
    print(json.dumps(ejecutar(), indent=2))
