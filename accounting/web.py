import sys
import logging
import argparse

from flask import Flask, g, jsonify, json, request

from accounting import Ledger, Account, Posting, Transaction, Amount
from accounting.transport import AccountingEncoder, AccountingDecoder


app = Flask('accounting')
app.config.from_pyfile('config.py')

ledger = Ledger(ledger_file=app.config['LEDGER_FILE'])


# These will convert output from our internal classes to JSON and back
app.json_encoder = AccountingEncoder
app.json_decoder = AccountingDecoder


@app.route('/')
def index():
    return 'Hello World!'


@app.route('/balance')
def balance_report():
    ''' Returns the balance report from ledger '''
    report_data = ledger.bal()

    return jsonify(balance_report=report_data)


@app.route('/parse-json', methods=['POST'])
def parse_json():
    r'''
    Parses a __type__-annotated JSON payload and debug-logs the decoded version
    of it.

    Example:

        wget http://127.0.0.1:5000/balance -O balance.json
        curl -X POST -H 'Content-Type: application/json' -d @balance.json \
            http://127.0.0.1/parse-json
        # Logging output (linebreaks added for clarity)
        DEBUG:accounting:json data: {'balance_report':
            [<Account "None" [
                <Amount $ 0>, <Amount KARMA 0>]
                [<Account "Assets" [
                    <Amount $ 50>, <Amount KARMA 10>]
                    [<Account "Assets:Checking" [
                        <Amount $ 50>] []>,
                     <Account "Assets:Karma Account" [
                        <Amount KARMA 10>] []>]>,
                 <Account "Expenses" [
                    <Amount $ 500>]
                    [<Account "Expenses:Blah" [
                        <Amount $ 250>]
                        [<Account "Expenses:Blah:Hosting" [
                            <Amount $ 250>] []>]>,
                     <Account "Expenses:Foo" [
                        <Amount $ 250>] [
                        <Account "Expenses:Foo:Hosting" [
                            <Amount $ 250>] []>]>]>,
                 <Account "Income" [
                    <Amount $ -550>,
                    <Amount KARMA -10>]
                    [<Account "Income:Donation" [
                        <Amount $ -50>] []>,
                     <Account "Income:Foo" [
                        <Amount $ -500>]
                        [<Account "Income:Foo:Donation" [
                            <Amount $ -500>] []>]>,
                     <Account "Income:Karma" [
                     <Amount KARMA -10>] []>]>]>]}
    '''
    app.logger.debug('json data: %s', request.json)
    return jsonify(foo='bar')


@app.route('/register')
def register_report():
    ''' Returns the register report from ledger '''
    report_data = ledger.reg()

    return jsonify(register_report=report_data)


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

    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.verbosity, 'INFO'))

    app.run(host=app.config['HOST'], port=app.config['PORT'])

if __name__ == '__main__':
    main()
