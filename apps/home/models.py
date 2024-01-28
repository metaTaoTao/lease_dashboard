# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps import db

from apps.authentication.util import hash_pass


class OrderSummary(db.Model):
    __tablename__ = 'OrderSummary'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(64))
    order_time = db.Column(db.String(64))
    device = db.Column(db.String(64))
    purchase_px = db.Column(db.String(64))
    official_px = db.Column(db.String(64))
    pay1 = db.Column(db.Float)
    pay2 = db.Column(db.Float)
    pay3 = db.Column(db.Float)
    pay4 = db.Column(db.Float)
    pay5 = db.Column(db.Float)
    pay6 = db.Column(db.Float)
    pay7 = db.Column(db.Float)
    pay8 = db.Column(db.Float)
    pay9 = db.Column(db.Float)
    pay10 = db.Column(db.Float)
    pay11 = db.Column(db.Float)
    pay12 = db.Column(db.Float)
    deposit = db.Column(db.Float)
    buydown = db.Column(db.Float)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.order_id)


class Cashflow(db.Model):
    __tablename__ = 'Cashflow'
    # cf_df = pd.DataFrame(columns=['order_id', 'seq','amount','due_dt','actual_pay_dt'])
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(64))
    seq = db.Column(db.Integer)
    amount = db.Column(db.Float)
    due_dt = db.Column(db.DATE)
    actual_pay_dt = db.Column(db.DATE)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.id)


class ClientInfo(db.Model):
    __tablename__ = 'ClientInfo'

    # client_info = pd.DataFrame(columns=['order_id', 'order_dt', 'maturity_dt','term','tenor','official_px','buydown','deposit'])
    order_id = db.Column(db.String(64), primary_key=True)
    order_dt = db.Column(db.DATE)
    maturity_dt = db.Column(db.DATE)
    term = db.Column(db.Integer)
    tenor = db.Column(db.Integer)
    official_px = db.Column(db.Float)
    buydown = db.Column(db.Float)
    deposit = db.Column(db.Float)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.order_id)
