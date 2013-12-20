# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later
import datetime
import uuid

from decimal import Decimal


class Transaction:
    def __init__(self, id=None, date=None, payee=None, postings=None,
                 metadata=None, _generate_id=False):
        if type(date) == datetime.datetime:
            date = date.date()

        self.id = id
        self.date = date
        self.payee = payee
        self.postings = postings
        self.metadata = metadata if metadata is not None else {}

        if _generate_id:
            self.generate_id()

    def generate_id(self):
        self.id = str(uuid.uuid4())

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return ('<{self.__class__.__name__} {self.id} {date}' +
                ' {self.payee} {self.postings}').format(
                    self=self,
                    date=self.date.strftime('%Y-%m-%d'))


class Posting:
    def __init__(self, account=None, amount=None, metadata=None):
        self.account = account
        self.amount = amount
        self.metadata = metadata if metadata is not None else {}

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return ('<{self.__class__.__name__} "{self.account}"' +
                ' {self.amount}>').format(self=self)


class Amount:
    def __init__(self, amount=None, symbol=None):
        self.amount = Decimal(amount)
        self.symbol = symbol

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return ('<{self.__class__.__name__} {self.symbol}' +
                ' {self.amount}>').format(self=self)


class Account:
    def __init__(self, name=None, amounts=None, accounts=None):
        self.name = name
        self.amounts = amounts
        self.accounts = accounts

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return ('<{self.__class__.__name__} "{self.name}" {self.amounts}' +
                ' {self.accounts}>').format(self=self)
