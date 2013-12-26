# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

import os
import sys
import subprocess
import logging
import time
import re
import pygit2

from datetime import datetime
from xml.etree import ElementTree
from contextlib import contextmanager

from accounting.exceptions import AccountingException, TransactionNotFound, \
    LedgerNotBalanced, TransactionIDCollision
from accounting.models import Account, Transaction, Posting, Amount
from accounting.storage import Storage

_log = logging.getLogger(__name__)


class Ledger(Storage):
    def __init__(self, app=None, ledger_file=None, ledger_bin=None):
        if app:
            ledger_file = app.config['LEDGER_FILE']

        if ledger_file is None:
            raise ValueError('ledger_file cannot be None')

        self.ledger_bin = ledger_bin or 'ledger'
        self.ledger_file = ledger_file
        _log.info('ledger file: %s', ledger_file)

        try:
            self.repository = pygit2.Repository(
                os.path.join(os.path.dirname(self.ledger_file), '.git'))
        except KeyError:
            self.repository = None
            _log.warning('ledger_file directory does not contain a .git'
                         ' directory, will not track changes.')

        # The signature used as author and committer in git commits
        self.signature = pygit2.Signature(
            name='accounting-api',
            email='accounting-api@accounting.example')

    def commit_changes(self, message):
        '''
        Commits any changes to :attr:`self.ledger_file` to the git repository
        '''
        if self.repository is None:
            return

        # Add the ledger file
        self.repository.index.read()
        self.repository.index.add(os.path.basename(self.ledger_file))
        tree_id = self.repository.index.write_tree()
        self.repository.index.write()

        parents = []
        try:
            parents.append(self.repository.head.target)
        except pygit2.GitError:
            _log.info('Repository has no head, creating initial commit')

        commit_id = self.repository.create_commit(
            'HEAD',
            self.signature,
            self.signature,
            message,
            tree_id,
            parents)

    def assemble_arguments(self, command=None):
        '''
        Returns a list of arguments suitable for :class:`subprocess.Popen`
        based on :attr:`self.ledger_bin` and :attr:`self.ledger_file`.
        '''
        args = [
            self.ledger_bin,
            '-f',
            self.ledger_file,
        ]
        if command is not None:
            args.append(command)

        return args

    def send_command(self, command):
        '''
        Creates a new ledger process with the specified :data:`command` and
        returns the output.

        Raises an :class:`~accounting.exceptions.AccountingException`-based
        Exception based on the ledger-cli stderr.
        '''
        _log.debug('Sending command: %r', command)
        _log.debug('Starting ledger...')
        p = subprocess.Popen(
            self.assemble_arguments(command=command),
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)

        output = p.stdout.read()
        stderr = p.stderr.read().decode('utf8')

        if stderr:
            lines = stderr.split('\n')
            if 'While balancing transaction from' in lines[1]:
                raise LedgerNotBalanced('\n'.join(lines[2:]))

            raise AccountingException(stderr)

        p.send_signal(subprocess.signal.SIGTERM)
        _log.debug('Waiting for ledger to shut down')
        p.wait()

        return output

    def add_transaction(self, transaction):
        '''
        Writes a transaction to the ledger file by opening it in 'ab' mode and
        writing a ledger transaction based on the
        :class:`~accounting.models.Transaction` instance in
        :data:`transaction`.
        '''
        if transaction.id is None:
            _log.debug('No ID found. Generating an ID.')
            transaction.generate_id()

        exists = self.get_transaction(transaction.id)

        if exists is not None:
            raise TransactionIDCollision(
                'A transaction with the id %s already exists: %s' %
                (transaction.id, exists))

        transaction.metadata.update({'Id': transaction.id})

        transaction_template = ('\n{date} {t.payee}\n'
                                '{metadata}'
                                '{postings}')

        metadata_template = '   ;{0}: {1}\n'

        # TODO: Generate metadata for postings
        posting_template = ('  {account} {p.amount.symbol}'
                            ' {p.amount.amount}\n')

        output = b''

        # XXX: Even I hardly understands what this does, however I indent it it
        # stays unreadable.
        output += transaction_template.format(
            date=transaction.date.strftime('%Y-%m-%d'),
            t=transaction,
            metadata=''.join([
                metadata_template.format(k, v)
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

        self.commit_changes('Added transaction %s' % transaction.id)

        _log.info('Added transaction %s', transaction.id)

        _log.debug('written to file: %s', output)

        return transaction.id

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

    def get_transactions(self):
        return self.reg()

    def get_transaction(self, transaction_id):
        transactions = self.get_transactions()

        for transaction in transactions:
            if transaction.id == transaction_id:
                return transaction

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
            try:
                id = metadata.pop('Id')
            except KeyError:
                _log.warning('Transaction on %s with payee %s does not have an'
                             ' Id attribute. A temporary ID will be used.',
                             date, payee)
                id = 'NO-ID'
            entries.append(
                Transaction(id=id, date=date, payee=payee, postings=postings,
                            metadata=metadata))

        return entries

    def delete_transaction(self, transaction_id):
        '''
        Delete a transaction from the ledger file.

        This method opens the ledger file, loads all lines into memory and
        looks for the transaction_id, then looks for the bounds of that
        transaction in the ledger file, removes all lines within the bounds of
        the transaction and removes them, then writes the lines back to the
        ledger file.

        Exceptions:

        -   RuntimeError: If all boundaries to the transaction are not found
        -   TransactionNotFound: If no such transaction_id can be found in
            :data:`self.ledger_file`
        '''
        f = open(self.ledger_file, 'r')

        lines = [i for i in f]

        # A mapping of line meanings and their line numbers as found by the
        # following logic
        semantic_lines = dict(
            id_location=None,
            transaction_start=None,
            next_transaction_or_eof=None
        )

        for i, line in enumerate(lines):
            if transaction_id in line:
                semantic_lines['id_location'] = i
                break

        if not semantic_lines['id_location']:
            raise TransactionNotFound(
                'No transaction with ID "{0}" found'.format(transaction_id))

        transaction_start_pattern = re.compile(r'^\S')

        cursor = semantic_lines['id_location'] - 1

        # Find the first line of the transaction
        while True:
            if transaction_start_pattern.match(lines[cursor]):
                semantic_lines['transaction_start'] = cursor
                break

            cursor -= 1

        cursor = semantic_lines['id_location'] + 1

        # Find the last line of the transaction
        while True:
            try:
                if transaction_start_pattern.match(lines[cursor]):
                    semantic_lines['next_transaction_or_eof'] = cursor
                    break
            except IndexError:
                # Set next_line_without_starting_space_or_end_of_file to
                # the cursor. The cursor will be an index not included in the
                # list of lines
                semantic_lines['next_transaction_or_eof'] = cursor
                break

            cursor += 1

        if not all(map(lambda v: v is not None, semantic_lines.values())):
            raise RuntimeError('Could not find all the values necessary for'
                               ' safe deletion of a transaction.')

        del_start = semantic_lines['transaction_start']

        if len(lines) == semantic_lines['next_transaction_or_eof']:
            _log.debug('There are no transactions below the transaction being'
                       ' deleted. The line before the first line of the'
                       ' transaction will be deleted.')
            # Delete the preceding line to make the file
            del_start -= 1

        _log.info('Removing transaction with ID: %s (lines %d-%d)',
                   transaction_id,
                   del_start,
                   semantic_lines['next_transaction_or_eof'])

        del lines[del_start:semantic_lines['next_transaction_or_eof']]

        with open(self.ledger_file, 'w') as f:
            for line in lines:
                f.write(line)

        self.commit_changes('Removed transaction %s' % transaction_id)

    def update_transaction(self, transaction):
        '''
        Update a transaction in the ledger file.

        Takes a :class:`~accounting.models.Transaction` object and removes
        the old transaction using :data:`transaction.id` from the passed
        :class:`~accounting.models.Transaction` instance and adds
        :data:`transaction` to the database.
        '''
        if not transaction.id:
            return AccountingException(('The transaction {0} has no'
                                        ' id attribute').format(transaction))

        old_transaction = self.get_transaction(transaction.id)

        self.delete_transaction(transaction.id)

        self.add_transaction(transaction)

        _log.info('Updated transaction %s', transaction.id)
        _log.debug('Updated transaction from: %s to: %s', old_transaction,
                   transaction)


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
