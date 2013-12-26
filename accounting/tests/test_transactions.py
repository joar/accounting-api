'''
Tests for accounting-api
'''
import os
import unittest
import tempfile
import logging
import copy
import uuid

from datetime import datetime
from decimal import Decimal

from flask import json

from accounting.web import app, init_ledger

from accounting.transport import AccountingEncoder, AccountingDecoder
from accounting.models import Transaction, Posting, Amount

#logging.basicConfig(level=logging.DEBUG)


class TransactionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.fd, app.config['LEDGER_FILE'] = tempfile.mkstemp()
        init_ledger()
        self.simple_transaction = Transaction(
            date=datetime.today(),
            payee='Joar',
            postings=[
                Posting('Assets:Checking', Amount('-133.7', 'USD')),
                Posting('Expenses:Foo', Amount('133.7', 'USD'))
            ]
        )

    def tearDown(self):
        os.close(self.fd)
        os.unlink(app.config['LEDGER_FILE'])

    def test_get_transactions(self):
        open(app.config['LEDGER_FILE'], 'w').write(
            '1400-12-21 Old stuff\n'
            '  ;Id: foo\n'
            '  Assets:Checking  -100 USD\n'
            '  Expenses:Tax  100 USD\n')
        rv = self.app.get('/transaction')

        json_transaction = (
            b'{\n'
            b'  "transactions": [\n'
            b'    {\n'
            b'      "__type__": "Transaction", \n'
            b'      "date": "1400-12-21", \n'
            b'      "id": "foo", \n'
            b'      "metadata": {}, \n'
            b'      "payee": "Old stuff", \n'
            b'      "postings": [\n'
            b'        {\n'
            b'          "__type__": "Posting", \n'
            b'          "account": "Assets:Checking", \n'
            b'          "amount": {\n'
            b'            "__type__": "Amount", \n'
            b'            "amount": "-100", \n'
            b'            "symbol": "USD"\n'
            b'          }, \n'
            b'          "metadata": {}\n'
            b'        }, \n'
            b'        {\n'
            b'          "__type__": "Posting", \n'
            b'          "account": "Expenses:Tax", \n'
            b'          "amount": {\n'
            b'            "__type__": "Amount", \n'
            b'            "amount": "100", \n'
            b'            "symbol": "USD"\n'
            b'          }, \n'
            b'          "metadata": {}\n'
            b'        }\n'
            b'      ]\n'
            b'    }\n'
            b'  ]\n'
            b'}')

        self.assertEqual(rv.get_data(), json_transaction)

    def _post_json(self, path, data, expect=200, **kw):
        response = self.app.post(
            path,
            content_type='application/json',
            data=json.dumps(data, cls=AccountingEncoder),
            **kw
        )

        self.assertEqual(response.status_code, expect)

        return self._decode_response(response)

    def _decode_response(self, response):
        return json.loads(response.data, cls=AccountingDecoder)

    def _get_json(self, path, expect=200, **kw):
        response = self.app.get(path, **kw)

        self.assertEqual(response.status_code, expect)

        return self._decode_response(response)

    def _open_json(self, method, path, expect=200, **kw):
        response = self.app.open(
            path,
            method=method.upper(),
            **kw
        )

        self.assertEqual(response.status_code, expect)

        return self._decode_response(response)

    def _add_simple_transaction(self, transaction_id=None):
        if transaction_id is None:
            transaction_id = str(uuid.uuid4())

        transaction = copy.deepcopy(self.simple_transaction)
        transaction.id = transaction_id

        response = self._post_json('/transaction', transaction)

        self.assertEqual(len(response['transaction_ids']), 1)
        self.assertEqual(response['status'], 'OK')

        response = self._get_json('/transaction/' + transaction.id)

        self.assertEqual(transaction_id, response['transaction'].id)

        self.assertEqual(response['transaction'], transaction)

        return transaction

    def test_post_transaction_without_id(self):
        transaction = copy.deepcopy(self.simple_transaction)

        response = self._post_json('/transaction', transaction)

        self.assertEqual(len(response['transaction_ids']), 1)
        self.assertEqual(response['status'], 'OK')

        transaction.id = response['transaction_ids'][0]

        response = self._get_json('/transaction/' + transaction.id)

        self.assertEqual(response['transaction'], transaction)

    def test_delete_transaction(self):
        transaction = copy.deepcopy(self.simple_transaction)

        response = self._post_json('/transaction', transaction)

        transaction_id = response['transaction_ids'][0]

        self.assertIsNotNone(transaction_id)

        response = self._open_json('DELETE',
                                  '/transaction/' + transaction_id)

        self.assertEqual(response['status'], 'OK')

        with self.assertRaises(ValueError):
            # ValueError thrown because the response does not contain any JSON
            response = self._get_json('/transaction/' + transaction_id, 404)

    def test_post_multiple_transactions(self):
        transactions = [
            Transaction(
                date=datetime.today(),
                payee='Rent',
                postings=[
                    Posting(
                        account='Assets:Checking',
                        amount=Amount(amount='-4600.00', symbol='SEK')
                    ),
                    Posting(
                        account='Expenses:Rent',
                        amount=Amount(amount='4600.00', symbol='SEK')
                    )
                ]
            ),
            Transaction(
                date=datetime.today(),
                payee='Hosting',
                postings=[
                    Posting(
                        account='Assets:Checking',
                        amount=Amount(amount='-700.00', symbol='SEK')
                    ),
                    Posting(
                        account='Expenses:Hosting',
                        amount=Amount(amount='700.00', symbol='SEK')
                    )
                ]
            )
        ]

        response = self._post_json('/transaction',
                                  {'transactions': transactions})

        self.assertEqual(len(response['transaction_ids']), 2)

        transactions[0].id = response['transaction_ids'][0]
        transactions[1].id = response['transaction_ids'][1]

        response = self._get_json('/transaction/' + transactions[0].id)

        self.assertEqual(transactions[0], response['transaction'])

        response = self._get_json('/transaction/' + transactions[1].id)

        self.assertEqual(transactions[1], response['transaction'])

    def test_update_transaction_payee(self):
        transaction = self._add_simple_transaction()

        transaction.payee = 'not Joar'

        response = self._post_json('/transaction/' + transaction.id,
                                   {'transaction': transaction})

        self.assertEqual(response['status'], 'OK')

        response = self._get_json('/transaction/'+ transaction.id)

        self.assertEqual(response['transaction'], transaction)

    def test_update_transaction_postings(self):
        transaction = self._add_simple_transaction()

        postings = [
            Posting(account='Assets:Checking',
                    amount=Amount(amount='-733.10', symbol='SEK')),
            Posting(account='Expenses:Bar',
                    amount=Amount(amount='733.10', symbol='SEK'))
        ]

        transaction.postings = postings

        response = self._post_json('/transaction/' + transaction.id,
                                   {'transaction': transaction})

        self.assertEqual(response['status'], 'OK')

        response = self._get_json('/transaction/' + transaction.id)

        self.assertEqual(response['transaction'], transaction)

    def test_post_unbalanced_transaction(self):
        transaction = Transaction(
            date=datetime.today(),
            payee='Unbalanced Transaction',
            postings=[
                Posting(account='Assets:Checking',
                        amount=Amount(amount='100.00', symbol='USD')),
                Posting(account='Income:Foo',
                        amount=Amount(amount='-100.01', symbol='USD'))
            ]
        )

        response = self._post_json('/transaction', transaction, expect=400)

        self.assertEqual(response['error']['type'], 'LedgerNotBalanced')

    def test_update_transaction_amounts(self):
        transaction = self._add_simple_transaction()
        response = self._get_json(
            '/transaction/' + transaction.id)

        transaction = response['transaction']

        for posting in transaction.postings:
            posting.amount.amount *= Decimal(1.50)

        response = self._post_json('/transaction/' + transaction.id,
                                   {'transaction': transaction})

        self.assertEqual(response['status'], 'OK')

        response = self._get_json('/transaction/' + transaction.id)

        self.assertEqual(response['transaction'], transaction)

    def test_delete_nonexistent_transaction(self):
        response = self._open_json('DELETE', '/transaction/I-do-not-exist',
                                   expect=404)

        self.assertEqual(response['error']['type'], 'TransactionNotFound')

    def test_post_transaction_with_metadata(self): pass


if __name__ == '__main__':
    unittest.main()
