# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

'''
This module contains the high-level webservice logic such as the Flask setup
and the Flask endpoints.
'''
import sys
import logging
import argparse

from flask import Flask, jsonify, request, render_template, abort
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from accounting.models import Transaction
from accounting.storage import Storage
from accounting.storage.ledgercli import Ledger
from accounting.storage.sql import SQLStorage
from accounting.transport import AccountingEncoder, AccountingDecoder
from accounting.exceptions import AccountingException, TransactionNotFound
from accounting.decorators import jsonify_exceptions, cors


app = Flask('accounting')
app.config.from_pyfile('config.py')

app.ledger = Storage()


def init_ledger():
    app.ledger = Ledger(app)


# These will convert output from our internal classes to JSON and back
app.json_encoder = AccountingEncoder
app.json_decoder = AccountingDecoder


@app.route('/')
def index():
    ''' Hello World! '''
    return 'Hello World!'

@app.route('/client')
def client():
    return render_template('client.html')


@app.route('/transaction', methods=['OPTIONS'])
@cors()
@jsonify_exceptions
def transaction_options():
    return jsonify(status='OPTIONS')


@app.route('/transaction/<string:transaction_id>', methods=['OPTIONS'])
@cors()
@jsonify_exceptions
def transaction_by_id_options(transaction_id=None):
    return jsonify(status='OPTIONS')


@app.route('/transaction', methods=['GET'])
@cors()
@jsonify_exceptions
def transaction_get_all(transaction_id=None):
    '''
    Returns the JSON-serialized output of :meth:`accounting.Ledger.reg`
    '''
    return jsonify(transactions=app.ledger.get_transactions())


@app.route('/transaction/<string:transaction_id>', methods=['GET'])
@cors()
@jsonify_exceptions
def transaction_get(transaction_id=None):
    transaction = app.ledger.get_transaction(transaction_id)

    if transaction is None:
        abort(404)

    return jsonify(transaction=transaction)


@app.route('/transaction/<string:transaction_id>', methods=['POST'])
@cors()
@jsonify_exceptions
def transaction_update(transaction_id=None):
    if transaction_id is None:
        raise AccountingException('The transaction ID cannot be None.')

    transaction = request.json['transaction']

    if transaction.id is not None and not transaction.id == transaction_id:
        raise AccountingException('The transaction data has an ID attribute'
                                  ' and it is not the same ID as in the path')
    elif transaction.id is None:
        transaction.id = transaction_id

    app.ledger.update_transaction(transaction)

    return jsonify(status='OK')


@app.route('/transaction/<string:transaction_id>', methods=['DELETE'])
@cors()
@jsonify_exceptions
def transaction_delete(transaction_id=None):
    if transaction_id is None:
        raise AccountingException('Transaction ID cannot be None')

    app.ledger.delete_transaction(transaction_id)

    return jsonify(status='OK')


@app.route('/transaction', methods=['POST'])
@cors()
@jsonify_exceptions
def transaction_post():
    '''
    REST/JSON endpoint for transactions.

    Current state:

    Takes a POST request with a ``transactions`` JSON payload and writes it to
    the ledger file.

    Requires the ``transactions`` payload to be __type__-annotated:

    .. code-block:: json

        {
          "transactions": [
            {
              "__type__": "Transaction",
              "date": "2013-01-01",
              "payee": "Kindly T. Donor",
              "postings": [
                {
                  "__type__": "Posting",
                  "account": "Income:Foo:Donation",
                  "amount": {
                    "__type__": "Amount",
                    "amount": "-100",
                    "symbol": "$"
                  }
                },
                {
                  "__type__": "Posting",
                  "account": "Assets:Checking",
                  "amount": {
                    "__type__": "Amount",
                    "amount": "100",
                    "symbol": "$"
                  }
                }
              ]
            }
        }

    becomes::

        2013-01-01 Kindly T. Donor
          Income:Foo:Donation                                         $ -100
          Assets:Checking                                              $ 100
    '''
    if not isinstance(request.json, Transaction):
        transactions = request.json.get('transactions')
    else:
        transactions = [request.json]

    if not transactions:
        raise AccountingException('No transaction data provided')

    transaction_ids = []

    for transaction in transactions:
        transaction_ids.append(app.ledger.add_transaction(transaction))

    return jsonify(status='OK', transaction_ids=transaction_ids)


def main(argv=None):
    prog = __name__
    if argv is None:
        prog = sys.argv[0]
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument('-v', '--verbosity',
                        default='INFO',
                        help=('Filter logging output. Possible values:' +
                              ' CRITICAL, ERROR, WARNING, INFO, DEBUG'))

    init_ledger()

    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.verbosity, 'INFO'))

    app.run(host=app.config['HOST'], port=app.config['PORT'])

if __name__ == '__main__':
    main()
