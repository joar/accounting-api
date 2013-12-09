import subprocess
import logging
import time

from datetime import datetime
from xml.etree import ElementTree
from contextlib import contextmanager

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
            _log.warning('Process is already locked')
            for i in range(1, 5):
                if i > 4:
                    raise RuntimeError('Ledger process is already locked')

                if not self.locked:
                    break
                else:
                    _log.info('Waiting for one second... %d/%d', i, 5)
                    time.sleep(1)


        process = self.get_process()

        self.locked = True
        _log.debug('lock enabled')

        yield process

        self.locked = False
        _log.debug('lock disabled')

    def assemble_arguments(self):
        return [
            self.ledger_bin,
            '-f',
            self.ledger_file,
        ]

    def init_process(self):
        _log.debug('starting ledger process')
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
            # _log.debug('reading data')

            line = p.stdout.read(1)  # XXX: This is a hack
            # _log.debug('line: %s', line)

            output += line

            if b'\n] ' in output:
                _log.debug('found prompt!')
                break

        output = output[:-3]  # Cut away the prompt

        _log.debug('output: %s', output)

        return output

    def send_command(self, p, command):
        # TODO: Should be extended to handle the locking and return the output
        _bytes = p.stdin.write(command + b'\n')
        p.stdin.flush()

        return _bytes

    def bal(self):
        output = None

        with self.locked_process() as p:
            _log.debug('aquired process lock')
            self.send_command(p, b'bal --format "%A|%t\\\\n"')
            _log.debug('sent command')

            output = self.read_until_prompt(p)

        if output is None:
            raise RuntimeError('bal call returned no output')

        accounts = []

        for line in output.split(b'\n'):
            name, balance =  line.decode('utf8').split('|')

            accounts.append(Account(name=name, balance=balance))

        return accounts

    def reg(self):
        output = None

        with self.locked_process() as p:
            _log.debug('aquired process lock')
            self.send_command(p, b'xml')

            output = self.read_until_prompt(p)

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

                postings.append(
                    Posting(account=account, amount=amount, symbol=symbol))

            entries.append(
                Transaction(date=date, payee=payee, postings=postings))

        return entries


class Transaction:
    def __init__(self, date=None, payee=None, postings=None):
        self.date = date
        self.payee = payee
        self.postings = postings

    def __repr__(self):
        return ('<{self.__class__.__name__} {date}' +
                ' {self.payee} {self.postings}').format(
                    self=self,
                    date=self.date.isoformat())

class Posting:
    def __init__(self, account=None, amount=None, symbol=None):
        self.account = account
        self.amount = amount
        self.symbol = symbol

    def __repr__(self):
        return ('<{self.__class__.__name__} "{self.account}"' +
                ' {self.symbol} {self.amount}>').format(self=self)


class Account:
    def __init__(self, name=None, balance=None):
        self.name = name
        self.balance = balance

    def __repr__(self):
        return '<{self.__class__.__name__}: "{self.name}" {self.balance} >'.format(
            self=self)


def main():
    ledger = Ledger(ledger_file='non-profit-test-data.ledger')
    print(ledger.bal())
    print(ledger.reg())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
