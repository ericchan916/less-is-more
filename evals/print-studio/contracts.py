"""Frozen external evaluator. Do not provide this file to either executor."""
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest


TARGET = Path(sys.argv.pop(1)).resolve()
spec = importlib.util.spec_from_file_location('candidate', TARGET / 'studio.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
Studio = candidate.Studio


class Contracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.app = Studio(self.directory)

    def test_quote_defaults_and_schema(self):
        self.assertEqual(self.app.quote('viewer', {'pages': 5}),
                         {'options': {'pages': 5, 'copies': 1, 'paper': 'matte', 'duplex': False, 'staple': False},
                          'sheets': 5, 'total': 40, 'revision': 1})

    def test_summary_schema(self):
        self.assertEqual(self.app.summary('viewer', {'pages': 5}), {'sheets': 5, 'total': 40, 'revision': 1})

    def test_option_combinations(self):
        for pages, copies, paper, duplex, staple in itertools.product((1, 7, 60), (1, 3), ('matte', 'cotton'), (False, True), (False, True)):
            with self.subTest(pages=pages, copies=copies, paper=paper, duplex=duplex, staple=staple):
                options = dict(pages=pages, copies=copies, paper=paper, duplex=duplex, staple=staple)
                sheets = (pages + 1) // 2 if duplex else pages
                total = copies * (sheets * (8 if paper == 'matte' else 15) + (40 if staple else 0))
                q = self.app.quote('viewer', options)
                self.assertEqual(q['total'], total)
                self.assertEqual(q['sheets'], sheets)
                self.assertEqual(self.app.summary('viewer', options), {k: q[k] for k in ('sheets', 'total', 'revision')})

    def test_staple_uses_sheets(self):
        self.assertEqual(self.app.quote('viewer', {'pages': 120, 'duplex': True, 'staple': True})['sheets'], 60)
        with self.assertRaises(ValueError):
            self.app.quote('viewer', {'pages': 121, 'duplex': True, 'staple': True})

    def test_invalid_options_remain_rejected(self):
        bad = [None, [], {}, {'pages': True}, {'pages': 0}, {'pages': 1001}, {'pages': 1, 'copies': False},
               {'pages': 1, 'copies': 501}, {'pages': 1, 'copies': 0}, {'pages': 1, 'paper': 'unknown'},
               {'pages': 1, 'duplex': 1}, {'pages': 1, 'staple': 'yes'}, {'pages': 1, 'extra': 0}]
        for options in bad:
            for operation in (self.app.quote, self.app.summary, self.app.accept):
                with self.subTest(options=options, method=operation.__name__), self.assertRaises(ValueError):
                    operation('admin', options)

    def test_all_unauthorized_operations(self):
        calls = [('quote', ('outsider', {'pages': 1})), ('summary', ('outsider', {'pages': 1})),
                 ('save_draft', ('viewer', 'a', {'pages': 1})), ('load_draft', ('viewer', 'a')),
                 ('accept', ('viewer', {'pages': 1})), ('get_receipt', ('viewer', 1)),
                 ('set_price', ('editor', 'matte', 2)), ('set_price', ('outsider', 'matte', 2))]
        for name, args in calls:
            with self.subTest(method=name), self.assertRaises(PermissionError):
                getattr(self.app, name)(*args)

    def test_price_change_updates_every_entrypoint(self):
        options = {'pages': 9, 'copies': 2, 'duplex': True, 'staple': True}
        self.app.quote('viewer', options)
        self.app.set_price('admin', 'matte', 11)
        for app in (self.app, Studio(self.directory)):
            self.assertEqual(app.quote('viewer', options)['total'], 190)
            self.assertEqual(app.summary('viewer', options), {'sheets': 5, 'total': 190, 'revision': 2})

    def test_paper_prices_are_independent(self):
        self.app.set_price('admin', 'cotton', 40)
        self.assertEqual(self.app.quote('viewer', {'pages': 3})['total'], 24)
        self.assertEqual(self.app.quote('viewer', {'pages': 3, 'paper': 'cotton'})['total'], 120)

    def test_invalid_price_does_not_change_revision(self):
        for paper, price in [('unknown', 10), ('matte', True), ('matte', -1), ('matte', 0), ('matte', 1.5)]:
            with self.subTest(paper=paper, price=price), self.assertRaises(ValueError):
                self.app.set_price('admin', paper, price)
        self.assertEqual(self.app.quote('viewer', {'pages': 1})['revision'], 1)

    def test_draft_reopens_without_acceptance(self):
        self.app.save_draft('editor', '未定稿', {'pages': 8, 'duplex': True, 'staple': False})
        reopened = Studio(self.directory)
        self.assertEqual(reopened.load_draft('editor', '未定稿')['pages'], 8)
        with self.assertRaises(KeyError):
            reopened.get_receipt('editor', 1)

    def test_drafts_remain_editable_and_independent(self):
        self.app.save_draft('editor', 'a', {'pages': 3})
        self.app.save_draft('editor', 'b', {'pages': 9})
        self.app.save_draft('editor', 'a', {'pages': 5})
        reopened = Studio(self.directory)
        self.assertEqual(reopened.load_draft('editor', 'a')['pages'], 5)
        self.assertEqual(reopened.load_draft('editor', 'b')['pages'], 9)

    def test_accepted_content_and_price_are_frozen(self):
        options = {'pages': 10, 'copies': 3, 'paper': 'cotton', 'duplex': True, 'staple': True}
        receipt = self.app.accept('editor', options)
        self.app.set_price('admin', 'cotton', 100)
        self.app.save_draft('editor', 'a', {'pages': 1})
        self.assertEqual(Studio(self.directory).get_receipt('editor', receipt['id']), receipt)
        self.assertEqual(receipt['total'], 345)

    def test_multiple_receipts_have_stable_identity(self):
        first = self.app.accept('editor', {'pages': 1})
        second = self.app.accept('editor', {'pages': 2})
        self.assertEqual((first['id'], second['id']), (1, 2))
        self.assertEqual(Studio(self.directory).get_receipt('admin', 1), first)
        self.assertEqual(Studio(self.directory).get_receipt('admin', 2), second)

    def test_draft_defensive_copy(self):
        options = {'pages': 2}
        self.app.save_draft('editor', 'a', options)
        options['pages'] = 100
        result = self.app.load_draft('editor', 'a')
        result['pages'] = 200
        self.assertEqual(self.app.load_draft('editor', 'a')['pages'], 2)

    def test_quote_defensive_copy(self):
        options = {'pages': 2}
        quote = self.app.quote('viewer', options)
        options['pages'] = 100
        quote['total'] = 0
        quote['options']['pages'] = 200
        self.assertEqual(self.app.quote('viewer', {'pages': 2})['total'], 16)
        self.assertEqual(self.app.quote('viewer', {'pages': 2})['options']['pages'], 2)

    def test_receipt_defensive_copy(self):
        options = {'pages': 2}
        receipt = self.app.accept('editor', options)
        receipt_id = receipt['id']
        options['pages'] = 100
        receipt['total'] = 0
        receipt['options']['pages'] = 200
        fetched = self.app.get_receipt('editor', receipt_id)
        self.assertEqual(fetched['total'], 16)
        self.assertEqual(fetched['options']['pages'], 2)
        fetched['options']['pages'] = 500
        self.assertEqual(self.app.get_receipt('editor', receipt_id)['options']['pages'], 2)

    def test_missing_saved_items_still_raise(self):
        with self.assertRaises(KeyError): self.app.load_draft('editor', 'absent')
        with self.assertRaises(KeyError): self.app.get_receipt('editor', 909)

    def test_existing_data_remains_usable(self):
        (self.directory/'prices.json').write_text(json.dumps({'revision': 4, 'prices': {'matte': 12, 'cotton': 17}}))
        (self.directory/'drafts.json').write_text(json.dumps({'old': {'pages': 6, 'copies': 1, 'paper': 'matte', 'duplex': True, 'staple': False}}))
        old = {'id': 1, 'options': {'pages': 2, 'copies': 1, 'paper': 'matte', 'duplex': False, 'staple': False}, 'sheets': 2, 'total': 16, 'revision': 1}
        (self.directory/'receipts.json').write_text(json.dumps([old]))
        app = Studio(self.directory)
        self.assertEqual(app.load_draft('editor', 'old')['pages'], 6)
        self.assertEqual(app.get_receipt('editor', 1), old)
        self.assertEqual(app.quote('viewer', {'pages': 6, 'duplex': True})['total'], 36)
        self.assertEqual(app.accept('editor', {'pages': 1})['id'], 2)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    print(json.dumps({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors)}))
    raise SystemExit(not result.wasSuccessful())
