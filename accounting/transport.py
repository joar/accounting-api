# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

from datetime import datetime

from flask import json

from accounting.exceptions import AccountingException
from accounting.models import Amount, Transaction, Posting, Account


class AccountingEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Account):
            return dict(
                __type__=o.__class__.__name__,
                name=o.name,
                amounts=o.amounts,
                accounts=o.accounts
            )
        elif isinstance(o, Transaction):
            return dict(
                __type__=o.__class__.__name__,
                id=o.id,
                date=o.date.strftime('%Y-%m-%d'),
                payee=o.payee,
                postings=o.postings,
                metadata=o.metadata
            )
        elif isinstance(o, Posting):
            return dict(
                __type__=o.__class__.__name__,
                account=o.account,
                amount=o.amount,
                metadata=o.metadata
            )
        elif isinstance(o, Amount):
            return dict(
                __type__=o.__class__.__name__,
                amount=str(o.amount),
                symbol=o.symbol
            )
        elif isinstance(o, AccountingException):
            return dict(
                type=o.__class__.__name__,
                message=o.message,
                transaction=getattr(o, 'transaction', None)
            )

        return json.JSONEncoder.default(self, o)


class AccountingDecoder(json.JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object)

    def dict_to_object(self, d):
        if '__type__' not in d:
            return d

        types = {c.__name__: c for c in [Amount, Transaction, Posting,
                                         Account, AccountingException]}

        _type = d.pop('__type__')

        if _type == 'Transaction':
            d['date'] = datetime.strptime(d['date'], '%Y-%m-%d')

        return types[_type](**d)
