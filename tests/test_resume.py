"""Integration checks for shared text, TeX escaping, and safe one-page publication."""
from html import unescape
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build as website
from resume import build_resume, link
from check_bundle import check_bundle


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
        self.data['companies']['innopolis']['name']['en'] = 'Shared Company'
        self.data['email'] = 'shared@example.com'
        website.build_site(self.data, output_root=self.root)
        html = unescape((self.root / 'site/index.html').read_text())
        self.assertIn(bullet, html)
        self.assertIn(event_statement, html)
        self.assertIn('Shared Name', html)
        self.assertIn('Shared Company', html)
        self.assertIn('mailto:shared@example.com', html)
        pdf = build_resume(self.data, root=self.root)
        self.assertIn(r'\documentclass[10pt,a4paper]{article}', (self.root / 'generated/ainur-karimov-cv.tex').read_text())
        text = subprocess.run(['pdftotext', str(pdf), '-'], capture_output=True, text=True, check=True).stdout
        for value in ['Shared Name', 'Shared Company', 'shared@example.com', 'R&D', '50%', 'under_score', '$10', '#1', '{literal}', 'missingfile']:
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

    def test_bundle_manifest_rejects_changed_content_and_tampered_pdf(self):
        source = self.root / 'content.json'
        source.write_text(json.dumps(self.data))
        website.build_all(source, self.root)
        check_bundle(self.root)
        original = source.read_text()
        source.write_text(original + '\n')
        with self.assertRaisesRegex(ValueError, 'changed after the last build'):
            check_bundle(self.root)
        source.write_text(original)
        with (self.root / 'site/assets/ainur-karimov-cv.pdf').open('ab') as file:
            file.write(b'tampered')
        with self.assertRaisesRegex(ValueError, 'Generated file changed'):
            check_bundle(self.root)

    def test_html_failure_does_not_replace_previous_website_or_pdf(self):
        destination = self.root / 'site'
        (destination / 'assets').mkdir(parents=True)
        (destination / 'index.html').write_text('previous website')
        (destination / 'assets/ainur-karimov-cv.pdf').write_bytes(b'previous PDF')
        source = self.root / 'content.json'
        source.write_text(json.dumps(self.data))
        with patch.object(website, 'build_site', side_effect=ValueError('invalid HTML template')):
            with self.assertRaisesRegex(ValueError, 'invalid HTML template'):
                website.build_all(source, self.root)
        self.assertEqual((destination / 'index.html').read_text(), 'previous website')
        self.assertEqual((destination / 'assets/ainur-karimov-cv.pdf').read_bytes(), b'previous PDF')

    def test_links_reject_tex_commands_and_unsupported_schemes(self):
        for url in ['javascript:alert(1)', 'https://example.com/{bad}', r'https://example.com/\input', 'https://example.com/bad path']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                link(url, 'label')


if __name__ == '__main__':
    unittest.main()
