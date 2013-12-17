# Part of accounting-api project:
# https://gitorious.org/conservancy/accounting-api
# License: AGPLv3-or-later

import json

from . import db


class Transaction(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    uuid = db.Column(db.String, unique=True, nullable=False)
    date = db.Column(db.DateTime)
    payee = db.Column(db.String())
    meta = db.Column(db.String())

    def as_dict(self):
        return dict(
            id=self.uuid,
            date=self.date,
            payee=self.payee,
            postings=[p.as_dict() for p in self.postings],
            metadata=json.loads(self.meta)
        )


class Posting(db.Model):
    id = db.Column(db.Integer(), primary_key=True)

    transaction_uuid = db.Column(db.String, db.ForeignKey('transaction.uuid'))
    transaction = db.relationship('Transaction', backref='postings')

    account = db.Column(db.String, nullable=False)

    amount_id = db.Column(db.Integer, db.ForeignKey('amount.id'))
    amount = db.relationship('Amount')

    meta = db.Column(db.String)

    def as_dict(self):
        return dict(
            account=self.account,
            amount=self.amount.as_dict(),
            metadata=json.loads(self.meta)
        )


class Amount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String)
    amount = db.Column(db.Numeric)

    def as_dict(self):
        return dict(
            symbol=self.symbol,
            amount=self.amount
        )
