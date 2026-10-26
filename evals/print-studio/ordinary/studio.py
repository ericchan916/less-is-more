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


def _sheets(options):
    return (options['pages'] + 1) // 2 if options['duplex'] else options['pages']


def _check(options):
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
    if result['staple'] and _sheets(result) > 60:
        raise ValueError('too many sheets to staple')
    return result


def _permit(role, operation):
    allowed = {'quote': {'viewer', 'editor', 'admin'},
               'edit': {'editor', 'admin'}, 'price': {'admin'}}
    if role not in allowed[operation]:
        raise PermissionError('not allowed')


class Studio:
    def __init__(self, directory):
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._prices = read_json(self._directory / 'prices.json',
                                 {'revision': 1, 'prices': {'matte': 8, 'cotton': 15}})
        self._save('prices', self._prices)
        self._drafts = read_json(self._directory / 'drafts.json', {})
        self._receipts = read_json(self._directory / 'receipts.json', [])

    def _save(self, name, value):
        write_json(self._directory / (name + '.json'), value)

    def quote(self, role, options):
        _permit(role, 'quote')
        options = _check(options)
        count = _sheets(options)
        total = options['copies'] * (count * self._prices['prices'][options['paper']]
                                     + (40 if options['staple'] else 0))
        return {'options': deepcopy(options), 'sheets': count,
                'total': total, 'revision': self._prices['revision']}

    def summary(self, role, options):
        value = self.quote(role, options)
        return {key: value[key] for key in ('sheets', 'total', 'revision')}

    def save_draft(self, role, name, options):
        _permit(role, 'edit')
        self._drafts[name] = deepcopy(_check(options))
        self._save('drafts', self._drafts)

    def load_draft(self, role, name):
        _permit(role, 'edit')
        return deepcopy(self._drafts[name])

    def accept(self, role, options):
        _permit(role, 'edit')
        receipt = {'id': len(self._receipts) + 1, **self.quote(role, options)}
        self._receipts.append(receipt)
        self._save('receipts', self._receipts)
        return deepcopy(receipt)

    def get_receipt(self, role, receipt_id):
        _permit(role, 'edit')
        for receipt in self._receipts:
            if receipt['id'] == receipt_id:
                return deepcopy(receipt)
        raise KeyError(receipt_id)

    def set_price(self, role, paper, unit):
        _permit(role, 'price')
        if paper not in self._prices['prices'] or type(unit) is not int or unit < 1:
            raise ValueError('invalid price')
        self._prices['prices'][paper] = unit
        self._prices['revision'] += 1
        self._save('prices', self._prices)
