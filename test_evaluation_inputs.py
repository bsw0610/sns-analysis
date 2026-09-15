"""Prediction-only corruption tests; all IDs/text come from the T1 fixture."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_evaluation_report as fixture

ROOT = Path(__file__).resolve().parent
# Run the real entry point in a child process with synthetic validator defaults.
RUN = '''
import runpy, sys
from pathlib import Path
import normalize_gold_standard_192 as n
n.DEFAULT_SOURCE, n.DEFAULT_SUPPLEMENT, n.DEFAULT_HYBRID = map(Path, sys.argv[1:4])
sys.argv = ['evaluate_v2_hybrid_192.py', *sys.argv[4:]]
runpy.run_module('evaluate_v2_hybrid_192', run_name='__main__')
'''


class PredictionInputTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.paths = fixture.GeneratedReportTests.build(Path(directory.name))
        self.predictions = Path(directory.name) / 'predictions.csv'
        with self.paths['hybrid'].open() as handle:
            self.rows = list(csv.DictReader(handle))
        self.fixed = {key: path.read_bytes() for key, path in self.paths.items()
                      if key != 'output'}

    def run_predictions(self, rows):
        with self.predictions.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=self.rows[0])
            writer.writeheader()
            writer.writerows(rows)
        p = self.paths
        result = subprocess.run(
            [sys.executable, '-c', RUN, str(p['source']), str(p['supplement']),
             str(p['hybrid']), '--gold', str(p['gold']), '--gold-189',
             str(p['gold_189']), '--predictions', str(self.predictions),
             '--output', str(p['output'])], cwd=ROOT, capture_output=True, text=True)
        for key, original in self.fixed.items():
            self.assertEqual(self.paths[key].read_bytes(), original)
        return result

    def reject(self, rows, reason, identity):
        output = self.paths['output']
        for existing in (False, True):
            with self.subTest(existing_report=existing):
                if output.exists():
                    output.unlink()
                if existing:
                    output.write_bytes(b'preserve existing report\x00\xff')
                    before = (output.read_bytes(), output.stat().st_mtime_ns)
                result = self.run_predictions(rows)
                # Check preservation even when an exit/diagnostic assertion fails.
                if existing:
                    self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), before)
                else:
                    self.assertFalse(output.exists(), result.stdout)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(reason, result.stderr)
                self.assertIn(identity, result.stderr)

    def test_missing(self):
        self.reject(self.rows[1:], 'missing prediction', self.rows[0]['投稿ID_文字列'])

    def test_duplicates(self):
        for outside in (False, True):
            with self.subTest(outside=outside):
                row = dict(self.rows[0])
                if outside:
                    row['投稿ID_文字列'] = 'outside-valid'
                self.reject(self.rows + [row, row] if outside else self.rows + [row],
                            'duplicate ID', row['投稿ID_文字列'])

    def test_empty_ids(self):
        for value in ('', '   '):
            with self.subTest(value=value):
                self.reject(self.rows + [dict(self.rows[0], 投稿ID_文字列=value)],
                            'empty ID', 'row 194')

    def test_invalid_values_inside_and_outside_gold(self):
        scores = json.loads(self.rows[0]['category_scores'])
        key = next(iter(scores))
        bad = [('sentiment_category', 'invalid', 'sentiment_category'),
               ('sentiment_category', '', 'sentiment_category')]
        structures = ['{', '[]', 'null', '1', '"text"', '{}',
                      json.dumps({k: v for k, v in scores.items() if k != key}),
                      json.dumps(dict(scores, unknown=0)),
                      json.dumps(scores)[:-1] + ', ' + json.dumps(key) + ': 0}']
        structures += [json.dumps(dict(scores, **{key: value}))
                       for value in (True, False, None, '2', float('nan'),
                                     float('inf'), -float('inf'), [], {})]
        structures += [json.dumps(scores).replace('0.0', '1e999', 1)]
        bad += [('category_scores', value, 'category_scores') for value in structures]
        for field, value, reason in bad:
            for outside in (False, True):
                with self.subTest(field=field, value=value, outside=outside):
                    row = dict(self.rows[0])
                    row[field] = value
                    if outside:
                        row['投稿ID_文字列'] = 'outside-invalid'
                    rows = self.rows + [row] if outside else [row] + self.rows[1:]
                    self.reject(rows, reason, row['投稿ID_文字列'])

    def test_valid_neutral_and_extra_rows_preserve_report(self):
        result = self.run_predictions(self.rows)
        self.assertEqual(result.returncode, 0, result.stderr)
        original = self.paths['output'].read_bytes()
        extra = dict(self.rows[0], 投稿ID_文字列='outside-valid')
        result = self.run_predictions(self.rows + [extra])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.paths['output'].read_bytes(), original)
        self.assertIn('192件', original.decode())


if __name__ == '__main__':
    unittest.main()
