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


class PriceBook:
    def __init__(self, directory):
        self.path = directory / 'prices.json'
        self.data = read_json(self.path, {'revision': 1, 'prices': {'matte': 8, 'cotton': 15}})
        write_json(self.path, self.data)

    def set_price(self, paper, unit):
        if paper not in self.data['prices'] or type(unit) is not int or unit < 1:
            raise ValueError('invalid price')
        self.data['prices'][paper] = unit
        self.data['revision'] += 1
        write_json(self.path, self.data)


class InputBoundary:
    def check(self, options):
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
        return result

    def permit(self, role, operation):
        allowed = {'quote': {'viewer', 'editor', 'admin'},
                   'edit': {'editor', 'admin'}, 'price': {'admin'}}
        if role not in allowed[operation]:
            raise PermissionError('not allowed')


class PreviewCalculator:
    def calculate(self, options, book):
        sheets = (options['pages'] + 1) // 2 if options['duplex'] else options['pages']
        total = options['copies'] * (sheets * book.data['prices'][options['paper']] + (40 if options['staple'] else 0))
        return {'options': deepcopy(options), 'sheets': sheets,
                'total': total, 'revision': book.data['revision']}


class SidebarCalculator:
    def calculate(self, options, book):
        sheets = (options['pages'] + 1) // 2 if options['duplex'] else options['pages']
        total = options['copies'] * (sheets * book.data['prices'][options['paper']] + (40 if options['staple'] else 0))
        return {'sheets': sheets, 'total': total, 'revision': book.data['revision']}


class QuoteCache:
    def __init__(self, directory):
        self.path = directory / 'quotes.json'
        self.data = read_json(self.path, {})

    def key(self, options):
        return json.dumps(options, sort_keys=True)

    def put(self, options, value):
        self.data[self.key(options)] = deepcopy(value)
        write_json(self.path, self.data)

    def get(self, options):
        return deepcopy(self.data.get(self.key(options)))

    def clear(self):
        self.data = {}
        write_json(self.path, self.data)


class DraftShelf:
    def __init__(self, directory):
        self.path = directory / 'drafts.json'
        self.data = read_json(self.path, {})

    def save(self, name, options):
        self.data[name] = deepcopy(options)
        write_json(self.path, self.data)

    def load(self, name):
        return deepcopy(self.data[name])


class ReceiptShelf:
    def __init__(self, directory):
        self.path = directory / 'receipts.json'
        self.data = read_json(self.path, [])

    def accept(self, quote):
        receipt = {'id': len(self.data) + 1, **deepcopy(quote)}
        self.data.append(receipt)
        write_json(self.path, self.data)
        return deepcopy(receipt)

    def get(self, receipt_id):
        for receipt in self.data:
            if receipt['id'] == receipt_id:
                return deepcopy(receipt)
        raise KeyError(receipt_id)


class Studio:
    def __init__(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.book = PriceBook(directory)
        self.boundary = InputBoundary()
        self.preview = PreviewCalculator()
        self.sidebar = SidebarCalculator()
        self.cache = QuoteCache(directory)
        self.drafts = DraftShelf(directory)
        self.receipts = ReceiptShelf(directory)

    def quote(self, role, options):
        self.boundary.permit(role, 'quote')
        options = self.boundary.check(options)
        value = self.cache.get(options)
        if value is None or value['revision'] != self.book.data['revision']:
            value = self.preview.calculate(options, self.book)
            self.cache.put(options, value)
        return deepcopy(value)

    def summary(self, role, options):
        self.boundary.permit(role, 'quote')
        options = self.boundary.check(options)
        return self.sidebar.calculate(options, self.book)

    def save_draft(self, role, name, options):
        self.boundary.permit(role, 'edit')
        self.drafts.save(name, self.boundary.check(options))

    def load_draft(self, role, name):
        self.boundary.permit(role, 'edit')
        return self.drafts.load(name)

    def accept(self, role, options):
        self.boundary.permit(role, 'edit')
        return self.receipts.accept(self.quote(role, options))

    def get_receipt(self, role, receipt_id):
        self.boundary.permit(role, 'edit')
        return self.receipts.get(receipt_id)

    def set_price(self, role, paper, unit):
        self.boundary.permit(role, 'price')
        self.book.set_price(paper, unit)
        self.cache.clear()
