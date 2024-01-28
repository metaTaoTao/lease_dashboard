from sqlalchemy import text
from apps import db
import pandas as pd
import datetime

class OrderAnalytics:
    def __init__(self):
        self.total_capital = "{:,}".format(6500000)
        self.balance = "{:,}".format(506888)
        self.order_summary_df = self.get_order_summary()
        self.today = datetime.date.today()
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.default_num = 28

    def get_order_summary(self):
        try:
            sql_query = text("select * from OrderSummary")  # to avoid SQL attack
            result = db.engine.execute(sql_query)
            results_as_dict = result.mappings().all()
            df = pd.DataFrame(results_as_dict)
            return df
        except Exception as e:
            return None

    def get_total_ar(self, cashflows, client_infos):
        try:
            lease_ar = cashflows.loc[cashflows['due_dt']> self.today]['amount'].sum()
            budydown_ar = client_infos.loc[client_infos['maturity_dt']> self.today]['buydown'].sum()
            deposit = client_infos.loc[client_infos['maturity_dt']> self.today]['deposit'].sum()

            net_ar = lease_ar + budydown_ar - deposit
            return int(net_ar)
        except Exception as e:
            return "{:,}".format(6500000)



    def get_cashflows(self):
        try:
            sql_query = text("select * from Cashflow")  # to avoid SQL attack
            result = db.engine.execute(sql_query)
            results_as_dict = result.mappings().all()
            df = pd.DataFrame(results_as_dict)
            df['due_dt'] = df.apply(lambda row: datetime.datetime.strptime(row['due_dt'], '%Y-%m-%d').date(), axis=1)
            return df
        except Exception as e:
            return None


    def get_client_info(self):
        try:
            sql_query = text("select * from ClientInfo")  # to avoid SQL attack
            result = db.engine.execute(sql_query)
            results_as_dict = result.mappings().all()
            df = pd.DataFrame(results_as_dict)
            df['maturity_dt'] = df.apply(lambda row: datetime.datetime.strptime(row['maturity_dt'], '%Y-%m-%d').date(), axis=1)
            df['order_dt'] = df.apply(lambda row: datetime.datetime.strptime(row['order_dt'], '%Y-%m-%d').date(),
                                         axis=1)
            return df
        except Exception as e:
            return None


    def get_cash_by_date(self, cashflows, client_infos, dt):
        try:
            rent = cashflows.loc[cashflows['due_dt']== dt]['amount'].sum()
            deposit = client_infos.loc[client_infos['order_dt']== dt]['deposit'].sum()
            buydown = client_infos.loc[client_infos['maturity_dt'] == dt]['buydown'].sum()

            res = rent + deposit + buydown
            return int(res)
        except Exception as e:
            return "{:,}".format(20000)
    def run(self):
        total_phone = len(self.order_summary_df) if not self.order_summary_df.empty else 0
        cashflows = self.get_cashflows()
        client_infos = self.get_client_info()
        total_ar = self.get_total_ar(cashflows, client_infos)
        today_cash = self.get_cash_by_date(cashflows, client_infos, self.today)
        tomorrow_cash =  self.get_cash_by_date(cashflows, client_infos, self.tomorrow)
        data = {
            'segment': 'index',
            'total_phone': total_phone,
            'total_capital': self.total_capital,
            'balance': self.balance,
            'total_ar': total_ar,
            'today_cash': today_cash,
            'tomorrow_cash': tomorrow_cash,
            'default_num': self.default_num
        }
        return data
