# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

class AccountingException(Exception):
    '''
    Used as a base for exceptions that are returned to the caller via the
    jsonify_exceptions decorator
    '''
    http_code = 500
    def __init__(self, message, **kw):
        self.message = message
        for key, value in kw.items():
            setattr(self, key, value)


class TransactionNotFound(AccountingException):
    http_code = 404


class LedgerNotBalanced(AccountingException):
    http_code = 400


class TransactionIDCollision(AccountingException):
    http_code = 400
