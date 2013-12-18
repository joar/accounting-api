# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

from abc import ABCMeta, abstractmethod

from accounting.exceptions import AccountingException


class Storage:
    '''
    ABC for accounting storage
    '''
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kw):
        pass

    @abstractmethod
    def get_transactions(self, *args, **kw):
        raise NotImplementedError

    @abstractmethod
    def get_transaction(self, *args, **kw):
        raise NotImplementedError

    @abstractmethod
    def get_account(self, *args, **kw):
        raise NotImplementedError

    @abstractmethod
    def get_accounts(self, *args, **kw):
        raise NotImplementedError

    @abstractmethod
    def add_transaction(self, transaction):
        raise NotImplementedError

    @abstractmethod
    def update_transaction(self, transaction):
        raise NotImplementedError

    @abstractmethod
    def delete_transaction(self, transaction_id):
        raise NotImplementedError

    @abstractmethod
    def reverse_transaction(self, transaction_id):
        raise NotImplementedError


class TransactionNotFound(AccountingException):
    pass
