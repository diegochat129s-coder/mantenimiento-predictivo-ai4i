"""Comprueba la entrega local sin publicar datos ni ejecutar modelos de nuevo."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import re
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
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
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
    required_powerbi = [
        'Mantenimiento.pbip', 'Mantenimiento.SemanticModel/definition.pbism',
        'Mantenimiento.Report/definition.pbir',
        'Mantenimiento.Report/definition/version.json',
        'Mantenimiento.Report/definition/report.json',
        'Mantenimiento.Report/definition/pages/pages.json',
        'Mantenimiento.Report/definition/pages/operacion/page.json',
    ]
    for relative in required_powerbi:
        path = ROOT / 'powerbi' / relative
        assert path.is_file(), f'Falta archivo obligatorio: {relative}'
        json.loads(path.read_text(encoding='utf-8'))
    version = json.loads((ROOT / 'powerbi/Mantenimiento.Report/definition/version.json').read_text(encoding='utf-8'))
    assert version['version'] == '2.0.0'
    assert version['$schema'].endswith('/definition/versionMetadata/1.0.0/schema.json')
    semantic = ROOT / 'powerbi/Mantenimiento.SemanticModel'
    if (semantic / 'model.bim').is_file():
        model = json.loads((semantic / 'model.bim').read_text(encoding='utf-8'))['model']
        tables = {t['name']: t for t in model['tables']}
    else:
        # Desktop guarda el modelo como TMDL; comprueba las referencias
        # utilizadas sin afirmar que esto sustituye al motor de Power BI.
        definition = semantic / 'definition'
        for name in ['database.tmdl', 'model.tmdl', 'relationships.tmdl', 'expressions.tmdl']:
            assert (definition / name).is_file(), f'Falta TMDL: {name}'
        tables = {}
        for path in (definition / 'tables').glob('*.tmdl'):
            content = path.read_text(encoding='utf-8')
            name = re.search(r'^table (.+)$', content, re.M).group(1).strip("'")
            tables[name] = {}
            for kind, key in [('column', 'columns'), ('measure', 'measures')]:
                names = re.findall(r"^\t" + kind + r" (?:'([^']+)'|([^\s=]+))", content, re.M)
                tables[name][key] = [{'name': quoted or plain} for quoted, plain in names]
        relations = []
        content = (definition / 'relationships.tmdl').read_text(encoding='utf-8')
        for block in re.split(r'^relationship ', content, flags=re.M)[1:]:
            relation = {}
            for side in ['from', 'to']:
                match = re.search(r'^\t' + side + r'Column: ([^.\s]+)\.([^\r\n]+)', block, re.M)
                assert match, f'Relación sin extremo {side}'
                relation[side + 'Table'], relation[side + 'Column'] = match.groups()
                cardinality = re.search(r'^\t' + side + r'Cardinality: (\w+)', block, re.M)
                relation[side + 'Cardinality'] = cardinality.group(1) if cardinality else ('many' if side == 'from' else 'one')
            relations.append(relation)
        model = {'relationships': relations}
    core_tables = {'fact_operacion', 'dim_tipo', 'dim_estado', 'dim_tiempo'}
    assert core_tables <= tables.keys()
    core_relations = [r for r in model['relationships'] if r['toTable'] in core_tables]
    assert {(r['fromTable'], r['fromColumn'], r['toTable'], r['toColumn']) for r in core_relations} == {
        ('fact_operacion', key, dimension, key)
        for key, dimension in [('tipo_id', 'dim_tipo'), ('estado_id', 'dim_estado'), ('tiempo_id', 'dim_tiempo')]
    }
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
        'tablas_powerbi': len(tables), 'relaciones_powerbi': len(model['relationships']),
        'tablas_negocio_powerbi': len(core_tables), 'relaciones_negocio_powerbi': len(core_relations),
        'visuales_powerbi': len(visuals),
        'powerbi_archivos_obligatorios_presentes': len(required_powerbi),
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
