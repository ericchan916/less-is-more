"""Synthetic local print studio. Amounts are integer demo units, no payment API."""
from copy import deepcopy
import json
from pathlib import Path


def read_json(path, default):
    if path.exists():
        return json.loads(path.read_text())
    return deepcopy(default)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False))


class Studio:
    def __init__(self, directory):
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._book = read_json(self._directory / 'prices.json',
                               {'revision': 1, 'prices': {'matte': 8, 'cotton': 15}})
        write_json(self._directory / 'prices.json', self._book)
        self._drafts = read_json(self._directory / 'drafts.json', {})
        self._receipts = read_json(self._directory / 'receipts.json', [])

    @staticmethod
    def _permit(role, operation):
        allowed = {'quote': {'viewer', 'editor', 'admin'},
                   'edit': {'editor', 'admin'}, 'price': {'admin'}}
        if role not in allowed[operation]:
            raise PermissionError('not allowed')

    @staticmethod
    def _options(options):
        if not isinstance(options, dict) or set(options) - {'pages', 'copies', 'paper', 'duplex', 'staple'}:
            raise ValueError('invalid options')
        result = {'copies': 1, 'paper': 'matte', 'duplex': False, 'staple': False, **options}
        if type(result.get('pages')) is not int or not 1 <= result['pages'] <= 1000:
            raise ValueError('invalid pages')
        if type(result['copies']) is not int or not 1 <= result['copies'] <= 500:
            raise ValueError('invalid copies')
        if result['paper'] not in ('matte', 'cotton'):
            raise ValueError('invalid paper')
        if type(result['duplex']) is not bool or type(result['staple']) is not bool:
            raise ValueError('invalid switches')
        sheets = (result['pages'] + 1) // 2 if result['duplex'] else result['pages']
        if result['staple'] and sheets > 60:
            raise ValueError('too many sheets to staple')
        return result, sheets

    def quote(self, role, options):
        self._permit(role, 'quote')
        options, sheets = self._options(options)
        total = options['copies'] * (sheets * self._book['prices'][options['paper']]
                                     + (40 if options['staple'] else 0))
        return {'options': deepcopy(options), 'sheets': sheets,
                'total': total, 'revision': self._book['revision']}

    def summary(self, role, options):
        quote = self.quote(role, options)
        return {key: quote[key] for key in ('sheets', 'total', 'revision')}

    def save_draft(self, role, name, options):
        self._permit(role, 'edit')
        options, _ = self._options(options)
        self._drafts[name] = deepcopy(options)
        write_json(self._directory / 'drafts.json', self._drafts)

    def load_draft(self, role, name):
        self._permit(role, 'edit')
        return deepcopy(self._drafts[name])

    def accept(self, role, options):
        self._permit(role, 'edit')
        receipt = {'id': len(self._receipts) + 1, **self.quote(role, options)}
        self._receipts.append(receipt)
        write_json(self._directory / 'receipts.json', self._receipts)
        return deepcopy(receipt)

    def get_receipt(self, role, receipt_id):
        self._permit(role, 'edit')
        for receipt in self._receipts:
            if receipt['id'] == receipt_id:
                return deepcopy(receipt)
        raise KeyError(receipt_id)

    def set_price(self, role, paper, unit):
        self._permit(role, 'price')
        if paper not in self._book['prices'] or type(unit) is not int or unit < 1:
            raise ValueError('invalid price')
        self._book['prices'][paper] = unit
        self._book['revision'] += 1
        write_json(self._directory / 'prices.json', self._book)
