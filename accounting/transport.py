from flask import json

from accounting import Amount, Transaction, Posting, Account

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
                date=o.date.strftime('%Y-%m-%d'),
                payee=o.payee,
                postings=o.postings
            )
        elif isinstance(o, Posting):
            return dict(
                __type__=o.__class__.__name__,
                account=o.account,
                amount=o.amount,
            )
        elif isinstance(o, Amount):
            return dict(
                __type__=o.__class__.__name__,
                amount=o.amount,
                symbol=o.symbol
            )

        return json.JSONEncoder.default(self, o)

class AccountingDecoder(json.JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object)

    def dict_to_object(self, d):
        if '__type__' not in d:
            return d

        types = {c.__name__ : c for c in [Amount, Transaction, Posting,
                                          Account]}

        _type = d.pop('__type__')

        return types[_type](**d)
