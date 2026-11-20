import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from etl_sqlserver import preparar, transformar


class PreparacionSqlServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(ROOT / 'data/raw/ai4i2020.csv')

    def test_fechas_reproducibles_tras_reordenar(self):
        first = transformar(self.raw)
        second = transformar(self.raw.sample(frac=1, random_state=13))
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first.fecha_operacion_simulada.iloc[0], '2026-01-01')
        self.assertEqual(first.fecha_operacion_simulada.iloc[49], '2026-01-01')
        self.assertEqual(first.fecha_operacion_simulada.iloc[50], '2026-01-02')
        self.assertEqual(first.fecha_operacion_simulada.iloc[-1], '2026-07-19')
        self.assertEqual(first.groupby('fecha_operacion_simulada').size().unique().tolist(), [50])

    def test_rechaza_nulos_duplicados_y_etiquetas_invalidas(self):
        for column, value in [('UDI', 2), ('Machine failure', 3), ('Torque [Nm]', None), ('Rotational speed [rpm]', 1.5)]:
            with self.subTest(column=column):
                bad = self.raw.copy()
                if column == 'Rotational speed [rpm]':
                    bad[column] = bad[column].astype(float)
                bad.loc[0, column] = value
                with self.assertRaises(ValueError):
                    transformar(bad)

    def test_dos_cargas_conservan_original_y_fechas(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'data/raw').mkdir(parents=True)
            raw = root / 'data/raw/ai4i2020.csv'
            shutil.copy2(ROOT / 'data/raw/ai4i2020.csv', raw)
            initial = hashlib.sha256(raw.read_bytes()).hexdigest()
            first, second = preparar(root), preparar(root)
            self.assertNotEqual(first.name, second.name)
            pd.testing.assert_frame_equal(pd.read_csv(first / 'ai4i_procesado.csv'), pd.read_csv(second / 'ai4i_procesado.csv'))
            self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), initial)
            self.assertEqual(json.loads((second / 'manifiesto.json').read_text())['discrepancias_etiquetas'], 27)
            pointer = (root / 'data/processed/sqlserver/actual.json').read_bytes()
            self.raw.iloc[:-1].to_csv(raw, index=False)
            with self.assertRaises(ValueError):
                preparar(root)
            self.assertEqual((root / 'data/processed/sqlserver/actual.json').read_bytes(), pointer)


if __name__ == '__main__':
    unittest.main()
