"""Extrae y valida AI4I, asigna fechas simuladas y prepara la carga SSIS."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COLUMNS = ['UDI', 'Product ID', 'Type', 'Air temperature [K]',
                  'Process temperature [K]', 'Rotational speed [rpm]',
                  'Torque [Nm]', 'Tool wear [min]', 'Machine failure',
                  'TWF', 'HDF', 'PWF', 'OSF', 'RNF']
TARGET_COLUMNS = ['udi', 'product_id', 'tipo', 'air_temperature_k',
                  'process_temperature_k', 'rotational_speed_rpm',
                  'torque_nm', 'tool_wear_min', 'estado_id',
                  'twf', 'hdf', 'pwf', 'osf', 'rnf']


def transformar(frame: pd.DataFrame) -> pd.DataFrame:
    """Cada UDI conserva su fecha en todas las recargas."""
    if list(frame.columns) != SOURCE_COLUMNS:
        raise ValueError('Las columnas del CSV no coinciden con AI4I 2020.')
    if len(frame) != 10000 or frame.isna().any().any():
        raise ValueError('Se requieren 10,000 registros completos.')
    result = frame.rename(columns=dict(zip(SOURCE_COLUMNS, TARGET_COLUMNS))).copy()
    numeric = [name for name in TARGET_COLUMNS if name not in ('product_id', 'tipo')]
    for name in numeric:
        result[name] = pd.to_numeric(result[name], errors='raise')
    if not np.isfinite(result[numeric].to_numpy(dtype=float)).all():
        raise ValueError('Hay números no finitos.')
    integers = ['udi', 'rotational_speed_rpm', 'tool_wear_min', 'estado_id',
                'twf', 'hdf', 'pwf', 'osf', 'rnf']
    if (result[integers] % 1 != 0).any().any():
        raise ValueError('Una columna entera contiene decimales.')
    result[integers] = result[integers].astype('int64')
    if set(result.udi) != set(range(1, 10001)) or result.udi.duplicated().any():
        raise ValueError('UDI debe ser único y cubrir 1 a 10000.')
    if not result.tipo.isin(['L', 'M', 'H']).all():
        raise ValueError('Tipo de producto desconocido.')
    if not result.product_id.str.match(r'^[LMH][0-9]+$').all():
        raise ValueError('Identificador de producto inválido.')
    if result.product_id.duplicated().any() or not result.product_id.str[0].eq(result.tipo).all():
        raise ValueError('Producto repetido o prefijo incompatible con Type.')
    flags = ['estado_id', 'twf', 'hdf', 'pwf', 'osf', 'rnf']
    if not result[flags].isin([0, 1]).all().all():
        raise ValueError('Las etiquetas deben ser 0 o 1.')
    if (result[['air_temperature_k', 'process_temperature_k', 'rotational_speed_rpm', 'torque_nm']] <= 0).any().any():
        raise ValueError('Las temperaturas, velocidad y torque deben ser positivos.')
    if (result.tool_wear_min < 0).any() or (result.process_temperature_k < result.air_temperature_k).any():
        raise ValueError('Desgaste o temperaturas inconsistentes.')
    result = result.sort_values('udi').reset_index(drop=True)
    result['fecha_operacion_simulada'] = (
        pd.Timestamp('2026-01-01') + pd.to_timedelta((result.udi - 1) // 50, unit='D')
    ).dt.strftime('%Y-%m-%d')
    result['tiempo_id'] = result.fecha_operacion_simulada.str.replace('-', '', regex=False).astype('int64')
    result['tipo_id'] = result.tipo.map({'L': 1, 'M': 2, 'H': 3})
    return result


def preparar(root: Path = ROOT, carga_id: str | None = None) -> Path:
    source = root / 'data/raw/ai4i2020.csv'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    processed = transformar(pd.read_csv(source))
    parent = root / 'data/processed/sqlserver'
    parent.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.UUID(carga_id)) if carga_id else str(uuid.uuid4())
    temporary = Path(tempfile.mkdtemp(prefix='preparando_', dir=parent))
    final = parent / run_id
    try:
        processed.to_csv(temporary / 'ai4i_procesado.csv', index=False, encoding='utf-8')
        staging = processed[TARGET_COLUMNS + ['fecha_operacion_simulada']].copy()
        staging.insert(0, 'carga_id', run_id)
        staging.to_csv(temporary / 'staging.csv', index=False, encoding='utf-8')
        mismatches = processed.estado_id.ne(processed[['twf', 'hdf', 'pwf', 'osf', 'rnf']].max(axis=1))
        processed.loc[mismatches].to_csv(temporary / 'discrepancias.csv', index=False)
        manifest = {
            'carga_id': run_id, 'filas': len(processed), 'sha256_original': before,
            'sha256_staging': hashlib.sha256((temporary / 'staging.csv').read_bytes()).hexdigest(),
            'fecha_preparacion_utc': datetime.now(timezone.utc).isoformat(),
            'fecha_inicial_simulada': processed.fecha_operacion_simulada.min(),
            'fecha_final_simulada': processed.fecha_operacion_simulada.max(),
            'discrepancias_etiquetas': int(mismatches.sum()),
            'regla': '2026-01-01 + floor((UDI - 1) / 50) días',
            'tipo_carga': 'FULL', 'estado': 'preparado_pendiente_sqlserver',
        }
        (temporary / 'manifiesto.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        if hashlib.sha256(source.read_bytes()).hexdigest() != before:
            raise RuntimeError('El original cambió durante la lectura.')
        temporary.rename(final)
        pointer = parent / ('actual_' + run_id + '.tmp')
        pointer.write_text(json.dumps({'directorio': str(final), 'carga_id': run_id}), encoding='utf-8')
        os.replace(pointer, parent / 'actual.json')
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return final


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raiz', type=Path, default=ROOT)
    parser.add_argument('--carga-id', default=None)
    args = parser.parse_args()
    print(preparar(args.raiz.resolve(), args.carga_id))
