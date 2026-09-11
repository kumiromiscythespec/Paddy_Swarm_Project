"""Regression checks using in-memory mutations; never modify the real ledger."""
import contextlib
import copy
import io
import sys
import unittest
from unittest.mock import patch
sys.dont_write_bytecode = True
import ledger
import validate_failure_ledger as cli

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.records, self.observations = ledger.load()

    def invalid(self, change):
        records = copy.deepcopy(self.records)
        change(records)
        with self.assertRaises((ValueError, TypeError)):
            ledger.validate(records, self.observations)

    def test_initial_count_and_views(self):
        self.assertEqual(ledger.validate(self.records, self.observations, initial=True), 50)
        for name, content in ledger.views(self.records, self.observations).items():
            self.assertEqual((ledger.LANE / name).read_bytes(), content.encode())
        view = ledger.render(self.records, self.observations)
        for text in ('50 / 1000', 'Remaining: 950', 'Progress: 5.0%'):
            self.assertIn(text, view)

    def test_all_nonphysical_classes_reject_counted(self):
        for classification in ledger.CLASSES - {'PHYSICAL_FAIL'}:
            with self.subTest(classification=classification):
                self.invalid(lambda rr: rr[0].update(classification=classification))

    def test_noncounted_statuses_and_classes_contribute_zero(self):
        for status in ledger.STATUSES - {'COUNTED'}:
            records = copy.deepcopy(self.records)
            records[0].update(count_status=status, official_count_member=False)
            self.assertEqual(ledger.validate(records, self.observations), 49)
        for classification in ledger.CLASSES - {'PHYSICAL_FAIL'}:
            records = copy.deepcopy(self.records)
            records[0].update(classification=classification, count_status='NOT_COUNTED', official_count_member=False)
            if classification == 'DUPLICATE':
                records[0]['duplicate_of'] = 'F-0002'
            self.assertEqual(ledger.validate(records, self.observations), 49)

    def test_ids_fields_dates(self):
        changes = [lambda rr: rr.append(copy.deepcopy(rr[0])),
                   lambda rr: rr[0].pop('test'),
                   lambda rr: rr[0].update(failure_id='F-00001'),
                   lambda rr: rr[0].update(date='2026-02-30', date_status='CONFIRMED'),
                   lambda rr: rr[0].update(date='20260908', date_status='CONFIRMED'),
                   lambda rr: rr[0].update(date=None, date_status='CONFIRMED'),
                   lambda rr: rr[0].update(official_count_member=1)]
        for change in changes:
            self.invalid(change)
        with self.assertRaises(ValueError):
            ledger.unique_keys([('failure_id', 'F-0001'), ('failure_id', 'F-0002')])

    def test_duplicates_and_stable_ids(self):
        self.invalid(lambda rr: rr[0].update(duplicate_of='F-0001'))
        self.invalid(lambda rr: rr[0].update(duplicate_of='F-9999', count_status='NOT_COUNTED', official_count_member=False))
        self.invalid(lambda rr: rr[0].update(duplicate_of='F-0002'))
        records = copy.deepcopy(self.records)
        records[31].update(count_status='NOT_COUNTED', official_count_member=False, duplicate_of='F-0018')
        self.assertEqual(ledger.validate(records, self.observations), 49)
        self.assertEqual(records[32]['failure_id'], 'F-0033')
        records[17].update(count_status='NOT_COUNTED', official_count_member=False, duplicate_of='F-0032')
        with self.assertRaises(ValueError):
            ledger.validate(records, self.observations)

    def test_new_counted_requires_documented_qualification(self):
        new = copy.deepcopy(self.records[0])
        new.update(failure_id='F-0055', legacy_record=False)
        records = self.records + [new]
        with self.assertRaises(ValueError):
            ledger.validate(records, self.observations)
        new['legacy_record'] = True
        with self.assertRaises(ValueError):
            ledger.validate(records, self.observations)
        new.update(legacy_record=False, detail_status='DOCUMENTED',
                   qualification={k: True for k in ledger.CHECKS})
        for field in ('component', 'specimen', 'test', 'expected_result', 'actual_result'):
            new[field] = 'SYNTHETIC TEST FIXTURE ONLY'
        self.assertEqual(ledger.validate(records, self.observations), 51)
        with self.assertRaises(ValueError):
            ledger.validate(records, self.observations, initial=True)
        for key in ledger.CHECKS:
            new['qualification'][key] = None
            with self.assertRaises(ValueError):
                ledger.validate(records, self.observations)
            new['qualification'][key] = True
        new['evidence'] = []
        with self.assertRaises(ValueError):
            ledger.validate(records, self.observations)

    def test_observations_never_count(self):
        self.observations[0]['count_status'] = 'COUNTED'
        with self.assertRaises(ValueError):
            ledger.validate(self.records, self.observations)

    def test_cli_nonzero_for_invalid_or_stale_view(self):
        with patch.object(sys, 'argv', ['validator']), contextlib.redirect_stderr(io.StringIO()):
            with patch.object(cli, 'load', side_effect=ValueError('bad data')):
                self.assertEqual(cli.main(), 1)
            with patch.object(ledger.Path, 'read_bytes', return_value=b'stale'):
                self.assertEqual(cli.main(), 1)

if __name__ == '__main__':
    unittest.main()
