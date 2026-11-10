"""Integration checks for shared text, TeX escaping, and safe one-page publication."""
from html import unescape
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build as website
from resume import build_resume, link


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = json.loads((ROOT / 'content.json').read_text())

    def test_one_edit_reaches_html_and_one_page_pdf_with_literal_tex_characters(self):
        bullet = r'R&D: 50% under_score $10 #1 {literal} ~ ^ \input{missingfile}'
        self.data['experience'][0]['bullets']['en'] = [bullet]
        event_statement = 'Presented the model at Inno Onco 2024 in Moscow.'
        self.data['presentations'][0]['statement']['en'] = event_statement
        self.data['name']['en'] = 'Shared Name'
        self.data['email'] = 'shared@example.com'
        shutil.copytree(ROOT / 'scripts', self.root / 'scripts')
        with patch.object(website, 'ROOT', self.root):
            website.build_site(self.data)
        html = unescape((self.root / 'site/index.html').read_text())
        self.assertIn(bullet, html)
        self.assertIn(event_statement, html)
        self.assertIn('Shared Name', html)
        self.assertIn('mailto:shared@example.com', html)
        pdf = build_resume(self.data, root=self.root)
        self.assertEqual((self.root / 'generated/twentysecondcv.cls').read_bytes(), (ROOT / 'twentysecondcv.cls').read_bytes())
        self.assertIn(r'\documentclass[a4paper]{twentysecondcv}', (self.root / 'generated/ainur-karimov-cv.tex').read_text())
        text = subprocess.run(['pdftotext', str(pdf), '-'], capture_output=True, text=True, check=True).stdout
        for value in ['Shared Name', 'shared@example.com', 'R&D', '50%', 'under_score', '$10', '#1', '{literal}', 'missingfile']:
            self.assertIn(value, text)
        # build_resume itself verifies exactly one A4 page and no missing/overflowing glyphs.
        self.assertEqual(text.count('\f'), 1)
        self.assertIn(event_statement, ' '.join(text.split()))

    def test_overflow_is_rejected_and_previous_download_is_preserved(self):
        destination = self.root / 'site/assets/ainur-karimov-cv.pdf'
        destination.parent.mkdir(parents=True)
        previous = (ROOT / 'site/assets/ainur-karimov-cv.pdf').read_bytes()
        destination.write_bytes(previous)
        self.data['experience'][0]['bullets']['en'] *= 120
        with self.assertRaisesRegex(ValueError, 'exactly one A4 page'):
            build_resume(self.data, root=self.root)
        self.assertEqual(destination.read_bytes(), previous)

    def test_absolute_sidebar_overflow_is_rejected(self):
        destination = self.root / 'site/assets/ainur-karimov-cv.pdf'
        destination.parent.mkdir(parents=True)
        previous = (ROOT / 'site/assets/ainur-karimov-cv.pdf').read_bytes()
        destination.write_bytes(previous)
        self.data['education'][0]['text']['en'] *= 40
        with self.assertRaisesRegex(ValueError, 'sidebar exceeds one A4 page'):
            build_resume(self.data, root=self.root)
        self.assertEqual(destination.read_bytes(), previous)

    def test_links_reject_tex_commands_and_unsupported_schemes(self):
        for url in ['javascript:alert(1)', 'https://example.com/{bad}', r'https://example.com/\input', 'https://example.com/bad path']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                link(url, 'label')


if __name__ == '__main__':
    unittest.main()
