import os

LEDGER_FILE = os.environ.get('LEDGER_FILE', None)
DEBUG = bool(int(os.environ.get('DEBUG', 0)))
PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '127.0.0.1')
