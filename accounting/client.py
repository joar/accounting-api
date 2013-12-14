import sys
import argparse
import json
import logging

from datetime import datetime
from decimal import Decimal

import requests

from accounting.models import Transaction, Posting, Amount
from accounting.transport import AccountingDecoder, AccountingEncoder

_log = logging.getLogger(__name__)


class Client:
    def __init__(self, host=None, json_encoder=None,
                 json_decoder=None):
        self.host = host or 'http://localhost:5000'
        self.json_encoder = json_encoder or AccountingEncoder
        self.json_decoder = json_decoder or AccountingDecoder

    def get_balance(self):
        balance = self.get('/balance')
        return balance['balance_report']

    def get(self, path):
        response = requests.get(self.host + path)

        return self._decode_response(response)

    def _decode_response(self, response):
        response_data = response.json(cls=self.json_decoder)

        _log.debug('response_data: %s', response_data)

        return response_data

    def post(self, path, payload, **kw):
        kw.update({'headers': {'Content-Type': 'application/json'}})
        kw.update({'data': json.dumps(payload, cls=self.json_encoder)})

        return self._decode_response(requests.post(self.host + path, **kw))

    def simple_transaction(self, from_acc, to_acc, amount):
        t = Transaction(
            date=datetime.today(),
            payee='PayPal donation',
            postings=[
                Posting(account=from_acc,
                        amount=Amount(symbol='$', amount=-amount)),
                Posting(account=to_acc,
                        amount=Amount(symbol='$', amount=amount))
            ]
        )

        return self.post('/transaction', {'transactions': [t]})

    def get_register(self):
        register = self.get('/transaction')

        return register['transactions']


def print_transactions(transactions):
    for transaction in transactions:
        print('{date} {t.payee:.<69}'.format(
            date=transaction.date.strftime('%Y-%m-%d'),
            t=transaction))

        for posting in transaction.postings:
            print(' ' + posting.account +
                  ' ' * (80 - len(posting.account) -
                         len(posting.amount.symbol) -
                         len(str(posting.amount.amount)) - 1 - 1) +
                  posting.amount.symbol + ' ' + str(posting.amount.amount))


def print_balance_accounts(accounts, level=0):
    for account in accounts:
        print(' ' * level + ' + {account.name}'.format(account=account) +
              ' ' + '-' * (80 - len(str(account.name)) - level))

        for amount in account.amounts:
            print(' ' * level + '   {amount.symbol} {amount.amount}'.format(
                amount=amount))

        print_balance_accounts(account.accounts, level+1)


def main(argv=None, prog=None):
    global HOST
    if argv is None:
        prog = sys.argv[0]
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=prog)
    actions = parser.add_subparsers(title='Actions', dest='action')

    insert = actions.add_parser('insert',
                                aliases=['in'])
    insert.add_argument('from_account')
    insert.add_argument('to_account')
    insert.add_argument('amount', type=Decimal)

    actions.add_parser('balance', aliases=['bal'])

    actions.add_parser('register', aliases=['reg'])

    parser.add_argument('-v', '--verbosity',
                        default='WARNING',
                        help=('Filter logging output. Possible values:' +
                              ' CRITICAL, ERROR, WARNING, INFO, DEBUG'))
    parser.add_argument('--host', default='http://localhost:5000')

    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.verbosity))

    client = Client(args.host)

    if args.action in ['insert', 'in']:
        print(client.simple_transaction(args.from_account, args.to_account,
                                        args.amount))
    elif args.action in ['balance', 'bal']:
        print_balance_accounts(client.get_balance())
    elif args.action in ['register', 'reg']:
        print_transactions(client.get_register())
    else:
        parser.print_help()

if __name__ == '__main__':
    sys.exit(main())
