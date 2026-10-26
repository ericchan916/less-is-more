import tempfile
import unittest
from studio import Studio


class Smoke(unittest.TestCase):
    def test_quote_and_summary(self):
        with tempfile.TemporaryDirectory() as d:
            app = Studio(d)
            quote = app.quote('viewer', {'pages': 5, 'copies': 2, 'duplex': True, 'staple': True})
            self.assertEqual(quote['total'], 128)
            self.assertEqual(app.summary('viewer', quote['options'])['total'], 128)

    def test_saved_content(self):
        with tempfile.TemporaryDirectory() as d:
            app = Studio(d)
            app.save_draft('editor', 'job', {'pages': 4})
            receipt = app.accept('editor', {'pages': 4})
            app.set_price('admin', 'matte', 20)
            reopened = Studio(d)
            self.assertEqual(reopened.load_draft('editor', 'job')['pages'], 4)
            self.assertEqual(reopened.get_receipt('editor', receipt['id'])['total'], 32)
            self.assertEqual(reopened.quote('viewer', {'pages': 4})['total'], 80)

    def test_permission(self):
        with tempfile.TemporaryDirectory() as d:
            app = Studio(d)
            with self.assertRaises(PermissionError):
                app.accept('viewer', {'pages': 4})


if __name__ == '__main__':
    unittest.main()
