class AccountingException(Exception):
    '''
    Used as a base for exceptions that are returned to the caller via the
    jsonify_exceptions decorator
    '''
    pass
