"""Comprueba la entrega local sin publicar datos ni ejecutar modelos de nuevo."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import nbformat
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from etl_sqlserver import transformar


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_etl_sqlserver.py')
    test = unittest.TextTestRunner(verbosity=2).run(suite)
    if not test.wasSuccessful():
        raise SystemExit(1)
    for path in [ROOT / 'src/etl_sqlserver.py', *list((ROOT / 'scripts').glob('*.py'))]:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    original = ROOT / 'data/raw/ai4i2020.csv'
    raw_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    assert raw_hash == 'dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e'
    frame = transformar(pd.read_csv(original))
    pd.testing.assert_frame_equal(frame, pd.read_csv(ROOT / 'data/processed/ai4i_fechas_simuladas.csv'))
    notebook = nbformat.read(ROOT / 'notebooks/02_ETL_SQLServer.ipynb', as_version=4)
    nbformat.validate(notebook)
    code = [cell for cell in notebook.cells if cell.cell_type == 'code']
    assert len(code) == 6 and all(cell.execution_count is not None for cell in code)
    assert not any(item.output_type == 'error' for cell in code for item in cell.outputs)
    model = json.loads((ROOT / 'powerbi/Mantenimiento.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
    tables = {t['name']: t for t in model['tables']}
    assert len(tables) == 4 and len(model['relationships']) == 3
    for relation in model['relationships']:
        for side in ['from', 'to']:
            assert relation[side + 'Column'] in {c['name'] for c in tables[relation[side + 'Table']]['columns']}
        assert relation['fromCardinality'] == 'many' and relation['toCardinality'] == 'one'
    visuals = list((ROOT / 'powerbi/Mantenimiento.Report').rglob('visual.json'))
    assert len(visuals) == 9
    for path in visuals:
        visual = json.loads(path.read_text(encoding='utf-8'))
        for role in visual['visual']['query']['queryState'].values():
            for projection in role['projections']:
                kind, field = next(iter(projection['field'].items()))
                entity = field['Expression']['SourceRef']['Entity']
                objects = tables[entity]['measures' if kind == 'Measure' else 'columns']
                assert field['Property'] in {obj['name'] for obj in objects}
    powershell_count = None
    if sys.platform == 'win32':
        command = '''$ErrorActionPreference='Stop'; $n=0
foreach($file in (Get-ChildItem scripts,ssis -Recurse -Filter *.ps1)) {
 $tokens=$null; $errors=$null
 [void][System.Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$errors)
 if($errors.Count) { throw ($errors | Out-String) }; $n++
}; Write-Output $n'''
        result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', command], cwd=ROOT,
                                capture_output=True, text=True, check=True)
        powershell_count = int(result.stdout.strip())
    evidence = {
        'verificado_utc': datetime.now(timezone.utc).isoformat(),
        'pruebas_python_aprobadas': test.testsRun,
        'notebook_celdas_ejecutadas_sin_error': len(code),
        'powershell_archivos_sintaxis_correcta': powershell_count,
        'tablas_powerbi': len(tables), 'relaciones_powerbi': 3, 'visuales_powerbi': len(visuals),
        'validacion_powerbi_en_este_script': 'Referencias de campos y relaciones; no apertura de Desktop.',
        'sha256_original': raw_hash, 'filas_procesadas': len(frame),
        'fallas': int(frame.estado_id.sum()), 'dias_simulados_utilizados': int(frame.tiempo_id.nunique()),
        'fecha_simulada_inicial': frame.fecha_operacion_simulada.min(),
        'fecha_simulada_final': frame.fecha_operacion_simulada.max(),
        'alcance': 'Comprobaciones locales; no ejecuta SQL Server, SSIS ni Power BI Desktop.',
    }
    target = ROOT / 'results/verificacion_preparacion_sqlserver.json'
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(evidence, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
