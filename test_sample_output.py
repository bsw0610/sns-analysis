"""Exercise the sample checker CLI using only isolated public sample files."""
import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write_rows(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


class SampleOutputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        sample = self.root / 'sample_data'
        sample.mkdir()
        for name in ('check_sample_output.py', 'sample_posts.csv'):
            shutil.copy2(ROOT / 'sample_data' / name, sample / name)
        shutil.copy2(ROOT / 'classify_sns_rule_based.py', self.root)
        self.expected = sample / 'sample_posts.csv'
        self.output = self.root / 'classified.csv'
        generated = subprocess.run(
            [sys.executable, str(self.root / 'classify_sns_rule_based.py'),
             '--input', str(self.expected), '--output', str(self.output)],
            capture_output=True, text=True)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        self.rows = read_rows(self.output)

    def check(self, reason=None, identity=None):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in (self.output, self.expected)}
        result = subprocess.run(
            [sys.executable, str(self.root / 'sample_data/check_sample_output.py'),
             str(self.output)], capture_output=True, text=True)
        for path, original in before.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), original)
        diagnostic = result.stdout + result.stderr
        if reason is None:
            self.assertEqual(result.returncode, 0, diagnostic)
            self.assertIn('30 rows classified, 21/30 match', diagnostic)
            self.assertIn('9 known disagreements reproduced exactly', diagnostic)
        else:
            self.assertNotEqual(result.returncode, 0, diagnostic)
            self.assertIn(reason, diagnostic)
            self.assertIn(identity, diagnostic)
        return result

    def test_normal(self):
        self.check()

    def test_reordered(self):
        write_rows(self.output, list(reversed(self.rows)))
        self.check()

    def test_missing(self):
        write_rows(self.output, self.rows[1:])
        self.check('missing ID', self.rows[0]['post_id'])

    def test_duplicate(self):
        write_rows(self.output, self.rows + [self.rows[0]])
        self.check('duplicate ID', self.rows[0]['post_id'])

    def test_missing_and_duplicate_same_count(self):
        write_rows(self.output, self.rows[1:] + [self.rows[1]])
        self.check('duplicate ID', self.rows[1]['post_id'])

    def test_unknown(self):
        for replace in (False, True):
            with self.subTest(replace=replace):
                unknown = dict(self.rows[0], post_id='synthetic-unknown')
                write_rows(self.output, (self.rows[1:] if replace else self.rows) + [unknown])
                self.check('unknown ID', 'synthetic-unknown')

    def test_empty_actual_id(self):
        for value in ('', '   '):
            with self.subTest(value=value):
                write_rows(self.output, [dict(self.rows[0], post_id=value)] + self.rows[1:])
                self.check('actual row 2: empty ID', 'row 2')

    def test_empty_expected_id(self):
        expected = read_rows(self.expected)
        for value in ('', '   '):
            with self.subTest(value=value):
                write_rows(self.expected, [dict(expected[0], post_id=value)] + expected[1:])
                self.check('expected row 2: empty ID', 'row 2')

    def test_duplicate_expected_id(self):
        expected = read_rows(self.expected)
        write_rows(self.expected, expected + [expected[0]])
        self.check('expected duplicate ID', expected[0]['post_id'])

    def test_changed_prediction(self):
        # Preserve apparent agreement and all aggregate counts: change both cells.
        row = dict(self.rows[0], intended_category='中立', sentiment_category='中立')
        write_rows(self.output, [row] + self.rows[1:])
        self.check('unexpected result for ID', row['post_id'])

    def test_changed_known_disagreement(self):
        rows = [dict(row) for row in self.rows]
        row = next(row for row in rows if row['intended_category'] != row['sentiment_category'])
        row['sentiment_category'] = row['intended_category']
        write_rows(self.output, rows)
        self.check('unexpected result for ID', row['post_id'])


if __name__ == '__main__':
    unittest.main()
