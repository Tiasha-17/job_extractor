import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx
import ollama
from extractor import ExtractionError, extract_posting
from storage import init_db, save_posting
from eval.real_world import prepare, load_cases, evaluate, FIELDS


class WorkflowTests(unittest.TestCase):
    def test_duplicate_and_distinct_postings(self):
        conn = init_db(':memory:')
        first = save_posting(conn, ' text ', {'company': 'A'})
        self.assertEqual(first, save_posting(conn, '\ntext\n', {'company': 'B'}))
        self.assertNotEqual(first, save_posting(conn, 'other', {}))
        self.assertEqual(conn.execute('select count(*) from postings').fetchone()[0], 2)
        conn.close()

    def test_legacy_duplicates_preserved(self):
        conn = init_db(':memory:')
        for text in [' text ', 'text']:
            conn.execute("insert into postings(saved_at, raw_text, extracted_json) values ('now', ?, '{}')", (text,))
        conn.commit()
        self.assertEqual(save_posting(conn, 'text', {}), 1)
        self.assertEqual(conn.execute('select count(*) from postings').fetchone()[0], 2)
        conn.close()

    def test_failed_save_rolls_back(self):
        conn = init_db(':memory:')
        with self.assertRaises(TypeError):
            save_posting(conn, 'text', {'bad': object()})
        self.assertFalse(conn.in_transaction)
        self.assertEqual(conn.execute('select count(*) from postings').fetchone()[0], 0)
        conn.close()

    def test_extraction_errors(self):
        errors = [(ConnectionError(), 'ollama serve'),
                  (httpx.ReadTimeout('timeout'), '120 seconds'),
                  (ollama.ResponseError('missing', 404), 'ollama pull')]
        for error, message in errors:
            with self.subTest(error=error), patch('extractor.ollama.Client') as client:
                client.return_value.chat.side_effect = error
                with self.assertRaisesRegex(ExtractionError, message):
                    extract_posting('posting')

    def test_bad_output_and_empty_input(self):
        for content in ['not json', '{}', '[]']:
            with patch('extractor.ollama.Client') as client:
                client.return_value.chat.return_value = SimpleNamespace(message=SimpleNamespace(content=content))
                with self.assertRaisesRegex(ExtractionError, 'invalid structured output'):
                    extract_posting('posting')
        with self.assertRaises(ExtractionError):
            extract_posting(' ')

    def test_manual_labels_and_failure_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'job.txt').write_text('A real posting', encoding='utf-8')
            prepare(folder)
            with self.assertRaises(FileExistsError):
                prepare(folder)
            with self.assertRaises(ValueError):
                load_cases(folder)
            label = dict(zip(FIELDS, ['Unknown', 'Full-time', 'Remote', 'Not mentioned']))
            label['sponsorship_evidence_quote'] = ''
            (folder / 'labels.json').write_text(json.dumps({'job.txt': label}))
            cases = load_cases(folder)
            report = evaluate(cases, lambda text: label)
            self.assertEqual(report['correct_fields'], 4)
            self.assertTrue(report['results'][0]['evidence_grounded'])
            def fail(text):
                raise ExtractionError('offline')
            report = evaluate(cases, fail)
            self.assertEqual((report['correct_fields'], report['total_fields'], report['failed_postings']), (0, 4, 1))

    def test_streamlit_offline_and_save_failure(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / 'test.db')
            with patch('storage.init_db', side_effect=lambda: init_db(db)), patch('extractor.extract_posting', side_effect=ExtractionError('Cannot connect. Run ollama serve')):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
                app.text_area[0].input('posting')
                app.button[0].click().run()
                self.assertFalse(app.exception)
                self.assertIn('ollama serve', app.error[0].value)
                with sqlite3.connect(db) as conn:
                    self.assertEqual(conn.execute('select count(*) from postings').fetchone()[0], 0)
            with patch('storage.init_db', side_effect=lambda: init_db(db)), patch('extractor.extract_posting', return_value={}), patch('storage.save_posting', side_effect=sqlite3.OperationalError('locked')):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
                app.text_area[0].input('posting')
                app.button[0].click().run()
                self.assertFalse(app.exception)
                self.assertIn('saving failed', app.error[0].value)
                self.assertTrue(app.json)


if __name__ == '__main__':
    unittest.main()
