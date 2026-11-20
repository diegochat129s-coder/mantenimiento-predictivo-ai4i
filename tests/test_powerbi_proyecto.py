import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from generar_powerbi import generate


class ProyectoPowerBiTest(unittest.TestCase):
    def test_generador_incluye_metadatos_y_modelo_relativo(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                generate('localhost', 'MantenimientoPredictivoDM', root=root)
            powerbi = root / 'powerbi'
            report = powerbi / 'Mantenimiento.Report'
            definition = report / 'definition'
            version = json.loads((definition / 'version.json').read_text(encoding='utf-8'))
            self.assertEqual(version['version'], '2.0.0')
            self.assertEqual(version['$schema'], 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json')
            for path in [definition / 'report.json', definition / 'pages/pages.json',
                         definition / 'pages/operacion/page.json']:
                self.assertTrue(path.is_file(), str(path))
            binding = json.loads((report / 'definition.pbir').read_text(encoding='utf-8'))
            model = (report / binding['datasetReference']['byPath']['path']).resolve()
            self.assertTrue((model / 'definition.pbism').is_file())
            self.assertTrue((model / 'model.bim').is_file())
            self.assertEqual(len(list(definition.rglob('visual.json'))), 9)


if __name__ == '__main__':
    unittest.main()
