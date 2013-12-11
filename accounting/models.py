from decimal import Decimal


class Transaction:
    def __init__(self, date=None, payee=None, postings=None):
        self.date = date
        self.payee = payee
        self.postings = postings

    def __repr__(self):
        return ('<{self.__class__.__name__} {date}' +
                ' {self.payee} {self.postings}').format(
                    self=self,
                    date=self.date.strftime('%Y-%m-%d'))


class Posting:
    def __init__(self, account=None, amount=None):
        self.account = account
        self.amount = amount

    def __repr__(self):
        return ('<{self.__class__.__name__} "{self.account}"' +
                ' {self.amount}>').format(self=self)


class Amount:
    def __init__(self, amount=None, symbol=None):
        self.amount = Decimal(amount)
        self.symbol = symbol

    def __repr__(self):
        return ('<{self.__class__.__name__} {self.symbol}' +
                ' {self.amount}>').format(self=self)


class Account:
    def __init__(self, name=None, amounts=None, accounts=None):
        self.name = name
        self.amounts = amounts
        self.accounts = accounts

    def __repr__(self):
        return ('<{self.__class__.__name__} "{self.name}" {self.amounts}' +
                ' {self.accounts}>').format(self=self)
