"""OpenDART Stage 0 retrieval, with a fake opener (no network)."""
import io
import json
import sys
import tempfile
import unittest
import urllib.parse
import zipfile
from pathlib import Path
from unittest.mock import patch

from harness_core import fetch_dart as D, runtime as h, universe as U
from harness_core.fetch import FetchError
from harness_core.universe_runner import BatchRunner, Options
from harness_core.universe_store import RunReader, Store

import universe_fixtures as F

KEY = 'test-key-0123456789abcdef'


def zip_of(name, data):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr(name, data)
    return buffer.getvalue()


def row(report, received, rcept):
    return {'report_nm': report, 'rcept_dt': received, 'rcept_no': rcept, 'corp_name': 'SK하이닉스'}


FILINGS = [row('사업보고서 (2025.12)', '20260317', '20260317000100'),
           row('[기재정정]사업보고서 (2025.12)', '20260401', '20260401000200'),
           row('반기보고서 (2026.06)', '20260814', '20260814000300'),
           row('분기보고서 (2026.03)', '20260515', '20260515000400'),
           row('분기보고서 (2025.09)', '20251114', '20251114000500'),
           row('반기보고서 (2025.06)', '20250814', '20250814000600'),
           row('분기보고서 (2025.03)', '20250515', '20250515000700'),
           row('분기보고서 (2024.09)', '20241114', '20241114000800'),
           row('사업보고서 (2024.12)', '20250318', '20250318000900'),
           row('주주총회소집공고', '20260228', '20260228001000'),
           row('분기보고서 (2026.09)', '20260925', '20260925001100')]    # after the cutoff


class FakeDart:
    def __init__(self):
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        parsed = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(parsed.query))
        assert query['crtfc_key'] == KEY
        if parsed.path.endswith('corpCode.xml'):
            return zip_of('CORPCODE.xml', '<result><list><corp_code>00164779</corp_code><corp_name>SK하이닉스</corp_name>'
                                          '<stock_code>000660</stock_code></list></result>'.encode('utf-8'))
        if parsed.path.endswith('list.json'):
            end = query['end_de']
            rows = [r for r in FILINGS if r['rcept_dt'] <= end]
            return json.dumps({'status': '000', 'total_page': 1, 'list': rows}).encode('utf-8')
        if parsed.path.endswith('document.xml'):
            return zip_of(f"{query['rcept_no']}.xml", f"<DOCUMENT>{query['rcept_no']}</DOCUMENT>".encode('utf-8'))
        raise AssertionError(url)


class DartTests(unittest.TestCase):
    def setUp(self):
        sleeper = patch.object(D.time, 'sleep', lambda s: None)
        sleeper.start()
        self.addCleanup(sleeper.stop)
        self.policy = json.loads((F.REPO/'config/intake.json').read_text(encoding='utf-8'))

    def test_stock_code_and_redaction(self):
        self.assertEqual([D.stock_code_of(x) for x in ('000660', '000660.KS', '000660-2026-09-22', 'LLY', '0006601')],
                         ['000660', '000660', '000660', None, None])
        self.assertNotIn(KEY, D.redact(f'https://x/api/list.json?crtfc_key={KEY}&corp_code=1'))

    def test_plan_respects_cutoff_and_amendments(self):
        fake = FakeDart()
        corp, name = D.resolve_corp_code('000660', KEY, fake)
        self.assertEqual((corp, name), ('00164779', 'SK하이닉스'))
        rows = D.list_filings(corp, '2026-09-22', KEY, fake)
        plan = D.plan(rows + [dict(FILINGS[-1], filing_date='2026-09-25', report_base='분기보고서 (2026.09)')],
                      self.policy, '2026-09-22')
        by_req = {}
        for r in plan['download']:
            by_req.setdefault(r['requirement'], []).append(r['rcept_no'])
        self.assertEqual(by_req['latest_annual'], ['20260401000200'])        # the amendment replaces the original
        self.assertNotIn('20260925001100', json.dumps(plan['download']))     # nothing after the cutoff
        shortfalls = {s['requirement']: s['shortfall'] for s in plan['shortfalls']}
        self.assertNotIn('trailing_quarters', shortfalls)                  # six interim periods (one shared with latest_interim)
        self.assertEqual(shortfalls.get('historical_annuals'), 1)            # 2 annual periods, 3 needed: reported, not invented
        self.assertIn('proxy_compensation', by_req)

    def test_download_names_match_intake_and_never_store_the_key(self):
        fake = FakeDart()
        rows = D.list_filings('00164779', '2026-09-22', KEY, fake)
        plan = D.plan(rows, self.policy, '2026-09-22')
        with tempfile.TemporaryDirectory() as tmp:
            saved = D.download(plan['download'], Path(tmp), KEY, fake)
            names = sorted(p.name for p in Path(tmp).iterdir())
            self.assertTrue(any(n.startswith('사업보고서') for n in names))
            self.assertNotIn(KEY, json.dumps(saved, ensure_ascii=False))
            from harness_core import intake
            documents = [{'document_id': f'D{i}', 'source_document': n, 'document_type': 'other'} for i, n in enumerate(names)]
            coverage = {r['id']: r for r in intake.coverage({'documents': documents}, self.policy)['requirements']}
            self.assertTrue(coverage['latest_annual']['met'] and coverage['latest_interim']['met'])

    def test_api_error_is_a_fetch_error(self):
        def refusing(url):
            return b'{"status":"020","message":"requests exceeded"}'
        with self.assertRaises(FetchError) as caught:
            D.resolve_corp_code('000660', KEY, refusing)
        self.assertIn('020', str(caught.exception))


class RunnerDartTests(unittest.TestCase):
    def test_krx_fetch_uses_env_and_key_never_reaches_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            F.copy_harness(root)
            with patch.object(h, 'ROOT', root):
                context = F.context_for('000660'); context['currency'] = 'KRW'
                h.dump_json(root/'.harness_inputs/000660/company_context.json', context)
                accepted, _, _ = U.normalize_entries(U.parse_txt('000660  # SK하이닉스\n'),
                                                     json.loads((root/'config/universe.json').read_text())['import'])
                self.assertEqual(accepted[0]['company_name'], 'SK하이닉스')
                with Store(root).transaction() as universe:
                    U.merge_import(universe, accepted, F.AS_OF, 'test', 'now', RunReader(h).run_as_of)
                with patch.dict('os.environ', {'HTTPS_PROXY': 'http://127.0.0.1:9', 'https_proxy': 'http://127.0.0.1:9'}):
                    BatchRunner(Store(root), RunReader(h), Options(dart_key=KEY)).run()
                row = Store(root).load()['tickers']['000660']
                self.assertEqual(row['run_status'], 'FAILED')                    # no network in tests
                self.assertIn('fetch 000660', row['last_error']['command'])
                for path in root.rglob('*'):
                    if path.is_file() and path.suffix in ('.json', '.log', '.md', '.csv', '.jsonl'):
                        self.assertNotIn(KEY, path.read_text(encoding='utf-8', errors='replace'), path)


if __name__ == '__main__':
    unittest.main()
