# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

class AccountingException(Exception):
    '''
    Used as a base for exceptions that are returned to the caller via the
    jsonify_exceptions decorator
    '''
    pass
