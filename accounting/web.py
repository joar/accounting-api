import logging

from flask import Flask, g, jsonify, json

from accounting import Ledger, Account, Posting, Transaction


logging.basicConfig(level=logging.DEBUG)
app = Flask('accounting')
app.config.from_pyfile('config.py')

ledger = Ledger(ledger_file=app.config['LEDGER_FILE'])

class AccountingEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Account):
            return dict(
                name=o.name,
                balance=o.balance
            )
        elif isinstance(o, Transaction):
            return dict(
                date=o.date.strftime('%Y-%m-%d'),
                payee=o.payee,
                postings=o.postings
            )
        elif isinstance(o, Posting):
            return dict(
                account=o.account,
                amount=o.amount,
                symbol=o.symbol
            )

        return json.JSONEncoder.default(self, o)

app.json_encoder = AccountingEncoder

@app.route('/')
def index():
    return 'Hello World!'

@app.route('/balance')
def balance_report():
    report_data = ledger.bal()

    return jsonify(balance_report=report_data)

@app.route('/register')
def register_report():
    report_data = ledger.reg()

    return jsonify(register_report=report_data)


def main():
    app.run(host=app.config['HOST'], port=app.config['PORT'])

if __name__ == '__main__':
    main()
