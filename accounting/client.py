import sys
import argparse
import json
import logging

from datetime import datetime
from decimal import Decimal

import requests

from accounting.models import Transaction, Posting, Amount
from accounting.transport import AccountingDecoder, AccountingEncoder

# TODO: Client should be a class

HOST = None


def insert_paypal_transaction(amount):
    t = Transaction(
        date=datetime.today(),
        payee='PayPal donation',
        postings=[
            Posting(account='Income:Donations:PayPal',
                    amount=Amount(symbol='$', amount=-amount)),
            Posting(account='Assets:Checking',
                    amount=Amount(symbol='$', amount=amount))
        ]
    )

    response = requests.post(HOST + '/transaction',
                             headers={'Content-Type': 'application/json'},
                             data=json.dumps({'transactions': [t]},
                                             cls=AccountingEncoder))

    print(response.json(cls=AccountingDecoder))


def get_balance():
    response = requests.get(HOST + '/balance')

    balance = response.json(cls=AccountingDecoder)

    _recurse_accounts(balance['balance_report'])


def _recurse_accounts(accounts, level=0):
    for account in accounts:
        print(' ' * level + ' + {account.name}'.format(account=account) +
              ' ' + '-' * (80 - len(str(account.name)) - level))
        for amount in account.amounts:
            print(' ' * level + '   {amount.symbol} {amount.amount}'.format(
                amount=amount))
        _recurse_accounts(account.accounts, level+1)


def main(argv=None, prog=None):
    global HOST
    if argv is None:
        prog = sys.argv[0]
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument('-p', '--paypal', type=Decimal)
    parser.add_argument('-v', '--verbosity',
                        default='WARNING',
                        help=('Filter logging output. Possible values:' +
                        ' CRITICAL, ERROR, WARNING, INFO, DEBUG'))
    parser.add_argument('-b', '--balance', action='store_true')
    parser.add_argument('--host', default='http://localhost:5000')
    args = parser.parse_args(argv)

    HOST = args.host

    logging.basicConfig(level=getattr(logging, args.verbosity))

    if args.paypal:
        insert_paypal_transaction(args.paypal)
    elif args.balance:
        get_balance()

if __name__ == '__main__':
    sys.exit(main())
