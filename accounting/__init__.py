import sys
import subprocess
import logging
import time

from datetime import datetime
from xml.etree import ElementTree
from contextlib import contextmanager

from accounting.models import Account, Transaction, Posting, Amount

_log = logging.getLogger(__name__)

class Ledger:
    def __init__(self, ledger_file=None, ledger_bin=None):
        if ledger_file is None:
            raise ValueError('ledger_file cannot be None')

        self.ledger_bin = ledger_bin or 'ledger'
        self.ledger_file = ledger_file
        _log.info('ledger file: %s', ledger_file)

        self.locked = False
        self.ledger_process = None

    @contextmanager
    def locked_process(self):
        if self.locked:
            raise RuntimeError('The process has already been locked,'
                               ' something\'s out of order.')

            # XXX: This code has no purpose in a single-threaded process
            timeout = 5  # Seconds

            for i in range(1, timeout + 2):
                if i > timeout:
                    raise RuntimeError('Ledger process is already locked')

                if not self.locked:
                    break
                else:
                    _log.info('Waiting for one second... %d/%d', i, timeout)
                    time.sleep(1)

        process = self.get_process()

        self.locked = True
        _log.debug('Lock enabled')

        yield process

        self.locked = False
        _log.debug('Lock disabled')

    def assemble_arguments(self):
        return [
            self.ledger_bin,
            '-f',
            self.ledger_file,
        ]

    def init_process(self):
        _log.debug('Starting ledger process...')
        self.ledger_process = subprocess.Popen(
            self.assemble_arguments(),
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)

        # Swallow the banner
        with self.locked_process() as p:
            self.read_until_prompt(p)

        return self.ledger_process

    def get_process(self):
        return self.ledger_process or self.init_process()

    def read_until_prompt(self, p):
        output = b''

        while True:
            line = p.stdout.read(1)  # XXX: This is a hack

            output += line

            if b'\n] ' in output:
                _log.debug('Found prompt!')
                break

        output = output[:-3]  # Cut away the prompt

        _log.debug('output: %s', output)

        return output

    def send_command(self, command):
        output = None

        with self.locked_process() as p:
            if isinstance(command, str):
                command = command.encode('utf8')

            p.stdin.write(command + b'\n')
            p.stdin.flush()

            output = self.read_until_prompt(p)

            self.ledger_process.send_signal(subprocess.signal.SIGTERM)
            _log.debug('Waiting for ledger to shut down')
            self.ledger_process.wait()
            self.ledger_process = None

            return output

    def add_transaction(self, transaction):
        '''
        Writes a transaction to the ledger file by opening it in 'ab' mode and
        writing a ledger transaction based on the Transaction instance in
        ``transaction``.
        '''
        if not transaction.metadata.get('Id'):
            transaction.generate_id()

        transaction_template = ('\n{date} {t.payee}\n'
                                '{tags}'
                                '{postings}')

        metadata_template = '   ;{0}: {1}\n'

        # TODO: Generate metadata for postings
        posting_template = ('  {account} {p.amount.symbol}'
                            ' {p.amount.amount}\n')

        output  = b''

        # XXX: Even I hardly understands what this does, however I indent it it
        # stays unreadable.
        output += transaction_template.format(
            date=transaction.date.strftime('%Y-%m-%d'),
            t=transaction,
            tags=''.join([
                metadata_template.format(k, v) \
                    for k, v in transaction.metadata.items()]),
            postings=''.join([posting_template.format(
                p=p,
                account=p.account + ' ' * (
                    80 - (len(p.account) + len(p.amount.symbol) +
                    len(str(p.amount.amount)) + 1 + 2)
                )) for p in transaction.postings
            ])
        ).encode('utf8')

        with open(self.ledger_file, 'ab') as f:
            f.write(output)

        _log.debug('written to file: %s', output)

    def bal(self):
        output = self.send_command('xml')

        if output is None:
            raise RuntimeError('bal call returned no output')

        accounts = []

        xml = ElementTree.fromstring(output.decode('utf8'))

        accounts = self._recurse_accounts(xml.find('./accounts'))

        return accounts

    def _recurse_accounts(self, root):
        accounts = []

        for account in root.findall('./account'):
            name = account.find('./fullname').text

            amounts = []

            # Try to find an account total value, then try to find the account
            # balance
            account_amounts = account.findall(
                './account-total/balance/amount') or \
                    account.findall('./account-amount/amount') or \
                    account.findall('./account-total/amount')

            if account_amounts:
                for amount in account_amounts:
                    quantity = amount.find('./quantity').text
                    symbol = amount.find('./commodity/symbol').text

                    amounts.append(Amount(amount=quantity, symbol=symbol))
            else:
                _log.warning('Account %s does not have any amounts', name)

            accounts.append(Account(name=name,
                                    amounts=amounts,
                                    accounts=self._recurse_accounts(account)))

        return accounts

    def reg(self):
        output = self.send_command('xml')

        if output is None:
            raise RuntimeError('reg call returned no output')

        entries = []

        reg_xml = ElementTree.fromstring(output.decode('utf8'))

        for transaction in reg_xml.findall('./transactions/transaction'):
            date = datetime.strptime(transaction.find('./date').text,
                                     '%Y/%m/%d')
            payee = transaction.find('./payee').text

            postings = []

            for posting in transaction.findall('./postings/posting'):
                account = posting.find('./account/name').text
                amount = posting.find('./post-amount/amount/quantity').text
                symbol = posting.find(
                    './post-amount/amount/commodity/symbol').text

                # Get the posting metadata
                metadata = {}

                values = posting.findall('./metadata/value')
                if values:
                    for value in values:
                        key = value.get('key')
                        value = value.find('./string').text

                        _log.debug('metadata: %s: %s', key, value)

                        metadata.update({key: value})

                postings.append(
                    Posting(account=account,
                            metadata=metadata,
                            amount=Amount(amount=amount, symbol=symbol)))

            # Get the transaction metadata
            metadata = {}

            values = transaction.findall('./metadata/value')
            if values:
                for value in values:
                    key = value.get('key')
                    value = value.find('./string').text

                    _log.debug('metadata: %s: %s', key, value)

                    metadata.update({key: value})

            # Add a Transaction instance to the list
            entries.append(
                Transaction(date=date, payee=payee, postings=postings,
                            metadata=metadata))

        return entries


def main(argv=None):
    import argparse
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbosity',
                        default='INFO',
                        help=('Filter logging output. Possible values:' +
                        ' CRITICAL, ERROR, WARNING, INFO, DEBUG'))

    args = parser.parse_args(argv[1:])
    logging.basicConfig(level=getattr(logging, args.verbosity, 'INFO'))
    ledger = Ledger(ledger_file='non-profit-test-data.ledger')
    print(ledger.bal())
    print(ledger.reg())


if __name__ == '__main__':
    sys.exit(main())
