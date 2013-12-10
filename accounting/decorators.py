from functools import wraps

from flask import jsonify

from accounting.exceptions import AccountingException


def jsonify_exceptions(func):
    '''
    Wraps a Flask endpoint and catches any AccountingException-based
    exceptions which are returned to the client as JSON.
    '''
    @wraps(func)
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except AccountingException as exc:
            return jsonify(error=exc)

    return wrapper
