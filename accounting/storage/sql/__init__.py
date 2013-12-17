# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

import logging
import json

from flask.ext.sqlalchemy import SQLAlchemy

from accounting.exceptions import AccountingException
from accounting.storage import Storage
from accounting.models import Transaction, Posting, Amount

_log = logging.getLogger(__name__)
db = SQLAlchemy()


class SQLStorage(Storage):
    def __init__(self, app=None):

        if not app:
            raise Exception('Missing app keyword argument')

        self.app = app
        db.init_app(app)

        from .models import Transaction as SQLTransaction, \
            Posting as SQLPosting, Amount as SQLAmount

        db.create_all()

        self.Transaction = SQLTransaction
        self.Posting = SQLPosting
        self.Amount = SQLAmount

    def get_transactions(self, *args, **kw):
        transactions = []

        for transaction in self.Transaction.query.all():
            dict_transaction = transaction.as_dict()
            dict_postings = dict_transaction.pop('postings')

            postings = []

            for dict_posting in dict_postings:
                dict_amount = dict_posting.pop('amount')
                posting = Posting(**dict_posting)
                posting.amount = Amount(**dict_amount)

                postings.append(posting)

            dict_transaction.update({'postings': postings})

            transactions.append(Transaction(**dict_transaction))

        return transactions

    def update_transaction(self, transaction):
        if transaction.id is None:
            raise AccountingException('The transaction id must be set for'
                                      ' update_transaction calls')

        _log.debug('DUMMY: Update transaction: %s', transaction)

    def add_transaction(self, transaction):
        if transaction.id is None:
            transaction.generate_id()

        _t = self.Transaction()
        _t.uuid = transaction.id
        _t.date = transaction.date
        _t.payee = transaction.payee
        _t.meta = json.dumps(transaction.metadata)

        db.session.add(_t)

        for posting in transaction.postings:
            _p = self.Posting()
            _p.transaction_uuid = transaction.id
            _p.account = posting.account
            _p.meta = json.dumps(posting.metadata)
            _p.amount = self.Amount(symbol=posting.amount.symbol,
                                    amount=posting.amount.amount)

            db.session.add(_p)

        db.session.commit()
