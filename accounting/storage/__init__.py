
class Storage:
    '''
    ABC for accounting storage
    '''
    def __init__(self, *args, **kw):
        raise NotImplementedError()

    def get_transactions(self, *args, **kw):
        raise NotImplementedError()

    def get_transaction(self, *args, **kw):
        raise NotImplementedError()

    def get_account(self, *args, **kw):
        raise NotImplementedError()

    def get_accounts(self, *args, **kw):
        raise NotImplementedError()
