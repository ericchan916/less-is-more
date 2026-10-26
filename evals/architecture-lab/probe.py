"""Synthetic ownership/recovery contracts; no network or production data.

The provider's token deduplication expires after ten simulated seconds.
Optional lookup is strongly consistent and retains accepted operations.
These are fixture assumptions, not claims about a real provider.
"""
import hashlib
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest


class SimulatedCrash(RuntimeError):
    pass


class NeedsReconciliation(RuntimeError):
    pass


def operation_id(tenant, key):
    return hashlib.sha256(json.dumps([tenant, key]).encode()).hexdigest()


class Provider:
    def __init__(self, directory, lookup=True):
        self.path = Path(directory) / 'provider.sqlite'
        self.lookup_available = lookup
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS operations '
                       '(id INTEGER PRIMARY KEY, op TEXT, tenant TEXT, payload TEXT, accepted INTEGER)')

    def accept(self, op, tenant, payload, now):
        with closing(sqlite3.connect(self.path)) as db, db:
            row = db.execute('SELECT id, tenant, payload FROM operations '
                             'WHERE op=? AND accepted>? ORDER BY id LIMIT 1',
                             (op, now - 10)).fetchone()
            if row is None:
                cursor = db.execute('INSERT INTO operations(op,tenant,payload,accepted) VALUES(?,?,?,?)',
                                    (op, tenant, payload, now))
                row = (cursor.lastrowid, tenant, payload)
        return dict(zip(('id', 'tenant', 'payload'), row))

    def lookup(self, op):
        if not self.lookup_available:
            raise NotImplementedError('No definitive operation lookup')
        with closing(sqlite3.connect(self.path)) as db, db:
            row = db.execute('SELECT id,tenant,payload FROM operations WHERE op=? ORDER BY id LIMIT 1',
                             (op,)).fetchone()
        return dict(zip(('id', 'tenant', 'payload'), row)) if row else None

    def count(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            return db.execute('SELECT count(*) FROM operations').fetchone()[0]


class AcceptanceOwner:
    """One local authority owns intent and confirmation, not the remote effect."""
    def __init__(self, directory, lookup=True):
        self.provider = Provider(directory, lookup)
        self.path = Path(directory) / 'requests.sqlite'
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS requests '
                       '(tenant TEXT, key TEXT, payload TEXT, op TEXT, receipt TEXT, attempt INTEGER, '
                       'PRIMARY KEY(tenant,key))')

    def submit(self, tenant, key, payload, now, fault=None):
        with closing(sqlite3.connect(self.path)) as db, db:
            row = db.execute('SELECT payload,op,receipt,attempt FROM requests WHERE tenant=? AND key=?',
                             (tenant, key)).fetchone()
            if row and row[0] != payload:
                raise ValueError('Same tenant/key with different intent')
            if row and row[2] is not None:
                return json.loads(row[2])
            fresh = row is None
            op = operation_id(tenant, key) if fresh else row[1]
            if fresh:
                db.execute('INSERT INTO requests VALUES(?,?,?,?,NULL,?)', (tenant, key, payload, op, now))
        if fault == 'before_provider':
            raise SimulatedCrash('Intent committed before provider call')
        receipt = None
        if not fresh:
            try:
                receipt = self.provider.lookup(op)
            except NotImplementedError as error:
                if not 0 <= now - row[3] < 10:
                    raise NeedsReconciliation('Outcome unknown; do not blindly resubmit') from error
                # The original window is still valid; retrying must not extend it.
            else:
                if receipt is None:
                    # Definitive absence permits a new attempt window in this fixture.
                    with closing(sqlite3.connect(self.path)) as db, db:
                        db.execute('UPDATE requests SET attempt=? WHERE tenant=? AND key=?',
                                   (now, tenant, key))
        if receipt is None:
            receipt = self.provider.accept(op, tenant, payload, now)
        if receipt['tenant'] != tenant or receipt['payload'] != payload:
            raise ValueError('Provider result does not match intent')
        if fault == 'after_provider':
            raise SimulatedCrash('Provider committed before local confirmation')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE requests SET receipt=? WHERE tenant=? AND key=?',
                       (json.dumps(receipt), tenant, key))
        return receipt


class Forwarder:
    def __init__(self, owner):
        self.owner = owner

    def submit(self, *args, **kwargs):
        return self.owner.submit(*args, **kwargs)


class LayeredIntake:
    def __init__(self, directory, lookup=True):
        self.forwarder = Forwarder(AcceptanceOwner(directory, lookup))

    def submit(self, *args, **kwargs):
        return self.forwarder.submit(*args, **kwargs)


class BlindRetry:
    """Counterexample: fewer local structures, incomplete business guarantees."""
    def __init__(self, directory):
        self.provider = Provider(directory)

    def submit(self, tenant, key, payload, now, fault=None):
        result = self.provider.accept(operation_id(tenant, key), tenant, payload, now)
        if fault == 'after_provider':
            raise SimulatedCrash('Local outcome lost')
        return result


class Contracts(unittest.TestCase):
    def test_normal_retry_and_reopen(self):
        for factory in (LayeredIntake, AcceptanceOwner):
            with self.subTest(factory=factory.__name__), tempfile.TemporaryDirectory() as directory:
                first = factory(directory).submit('a', 'k', 'doc', 0)
                self.assertEqual(factory(directory).submit('a', 'k', 'doc', 60), first)
                self.assertEqual(Provider(directory).count(), 1)

    def test_tenant_scope(self):
        for factory in (LayeredIntake, AcceptanceOwner):
            with self.subTest(factory=factory.__name__), tempfile.TemporaryDirectory() as directory:
                owner = factory(directory)
                a = owner.submit('a', 'k', 'doc-a', 0)
                b = owner.submit('b', 'k', 'doc-b', 1)
                self.assertNotEqual(a['id'], b['id'])
                self.assertEqual(b['tenant'], 'b')

    def test_conflicting_intent_is_rejected_before_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = AcceptanceOwner(directory)
            owner.submit('a', 'k', 'doc-a', 0)
            with self.assertRaises(ValueError):
                owner.submit('a', 'k', 'doc-b', 60)
            self.assertEqual(owner.provider.count(), 1)

    def test_remote_success_before_confirmation_recovers_without_duplicate(self):
        for factory in (LayeredIntake, AcceptanceOwner):
            with self.subTest(factory=factory.__name__), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(SimulatedCrash):
                    factory(directory).submit('a', 'k', 'doc', 0, fault='after_provider')
                result = factory(directory).submit('a', 'k', 'doc', 60)
                self.assertEqual(result['id'], 1)
                self.assertEqual(Provider(directory).count(), 1)

    def test_unconfirmed_intent_cannot_change_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SimulatedCrash):
                AcceptanceOwner(directory).submit('a', 'k', 'doc', 0, fault='after_provider')
            with self.assertRaises(ValueError):
                AcceptanceOwner(directory).submit('a', 'k', 'different', 60)
            self.assertEqual(Provider(directory).count(), 1)

    def test_crash_before_remote_can_resume_when_absence_is_definitive(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SimulatedCrash):
                AcceptanceOwner(directory).submit('a', 'k', 'doc', 0, fault='before_provider')
            self.assertEqual(Provider(directory).count(), 0)
            self.assertEqual(AcceptanceOwner(directory).submit('a', 'k', 'doc', 60)['id'], 1)

    def test_no_lookup_preserves_unknown_instead_of_claiming_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SimulatedCrash):
                AcceptanceOwner(directory, lookup=False).submit('a', 'k', 'doc', 0, fault='after_provider')
            with self.assertRaises(NeedsReconciliation):
                AcceptanceOwner(directory, lookup=False).submit('a', 'k', 'doc', 60)
            self.assertEqual(Provider(directory).count(), 1)

    def test_no_lookup_can_retry_inside_the_known_window(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SimulatedCrash):
                AcceptanceOwner(directory, lookup=False).submit('a', 'k', 'doc', 0, fault='after_provider')
            result = AcceptanceOwner(directory, lookup=False).submit('a', 'k', 'doc', 5)
            self.assertEqual(result['id'], 1)
            self.assertEqual(Provider(directory).count(), 1)

    def test_retry_does_not_extend_the_original_deduplication_window(self):
        with tempfile.TemporaryDirectory() as directory:
            for now in (0, 5):
                with self.assertRaises(SimulatedCrash):
                    AcceptanceOwner(directory, lookup=False).submit('a', 'k', 'doc', now, fault='after_provider')
            with self.assertRaises(NeedsReconciliation):
                AcceptanceOwner(directory, lookup=False).submit('a', 'k', 'doc', 10)
            self.assertEqual(Provider(directory).count(), 1)

    def test_blind_retry_is_a_real_counterexample_after_window_expiry(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SimulatedCrash):
                BlindRetry(directory).submit('a', 'k', 'doc', 0, fault='after_provider')
            BlindRetry(directory).submit('a', 'k', 'doc', 60)
            self.assertEqual(Provider(directory).count(), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
