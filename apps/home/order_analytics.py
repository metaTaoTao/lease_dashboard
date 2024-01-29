from sqlalchemy import text
from apps import db
import pandas as pd
import datetime


class OrderAnalytics:
    def __init__(self):
        self.total_capital = 6500000
        self.balance = 506888
        self.today = datetime.date.today()
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.yesterday = self.today + datetime.timedelta(days=-1)
        self.lastweek = self.today + datetime.timedelta(days=-7)

    def get_order_summary(self):
        try:
            sql_query = text("select * from OrderSummary")  # to avoid SQL attack
            result = db.engine.execute(sql_query)
            results_as_dict = result.mappings().all()
            df = pd.DataFrame(results_as_dict)
            df['order_dt'] = df.apply(lambda row: self.convert_order_time(row['order_time']), axis=1)
            return df
        except Exception as e:
            return None

    def convert_order_time(self, order_time):
        if isinstance(order_time, datetime.datetime):
            order_dt = order_time.date()
        else:
            order_dt = datetime.datetime.strptime(order_time.replace('\n', ''), '%Y-%m-%d %H:%M:%S').date()
        return order_dt

    def get_total_ar(self, cashflows, client_infos):
        res = []
        try:
            for d in [self.today, self.yesterday, self.lastweek]:
                lease_ar = cashflows.loc[cashflows['due_dt'] > d]['amount'].sum()
                budydown_ar = client_infos.loc[client_infos['maturity_dt'] > d]['buydown'].sum()
                deposit = client_infos.loc[client_infos['maturity_dt'] > self.today]['deposit'].sum()

                net_ar = lease_ar + budydown_ar - deposit
                res.append(int(net_ar))
            return res
        except Exception as e:
            return [0, 0, 0]

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
            df['maturity_dt'] = df.apply(lambda row: datetime.datetime.strptime(row['maturity_dt'], '%Y-%m-%d').date(),
                                         axis=1)
            df['order_dt'] = df.apply(lambda row: datetime.datetime.strptime(row['order_dt'], '%Y-%m-%d').date(),
                                      axis=1)
            return df
        except Exception as e:
            return None

    def get_cash_by_date(self, cashflows, client_infos, dt):
        try:
            rent = cashflows.loc[cashflows['due_dt'] == dt]['amount'].sum()
            deposit = client_infos.loc[client_infos['order_dt'] == dt]['deposit'].sum()
            buydown = client_infos.loc[client_infos['maturity_dt'] == dt]['buydown'].sum()

            res = rent + deposit + buydown
            return int(res)
        except Exception as e:
            return 20000

    def get_default_num(self, cashflows):
        orderid_list = cashflows['order_id'].unique().tolist()
        default = 0
        for order_id in orderid_list:
            cf = cashflows[cashflows['order_id'] == order_id]
            # find the first None actual pay date
            first_none = cf[cf['actual_pay_dt'].isnull()].iloc[0]
            first_none_due_dt = first_none['due_dt']
            if first_none_due_dt < self.today:
                default += 1
        return default

    def get_total_phone_by_date(self, df):
        res = []
        if not df.empty:
            for d in [self.today, self.yesterday, self.lastweek]:
                phone_num = len(df[df['order_dt'] <= d])
                res.append(phone_num)
            return res
        else:
            return [0, 0, 0]

    def _generate_json_format(self, df_contractual, df_real):

        res = {
            "daily": {
                "datasets": [ {"data": df_contractual['amount'].tolist(), "label":"应收账款"},
                              {"data": df_real['amount'].tolist()+[None for i in range(len(df_contractual)-len(df_real))], "label":"实收账款"}],
                "labels": [x.strftime("%Y-%m-%d") for x in df_contractual.index.tolist()]
            }
        }

        return res
    def get_cashflow_chart_data(self):
        cashflows = self.get_cashflows()
        df_contractual =pd.pivot_table(cashflows, values='amount', index=['due_dt'], aggfunc="sum")
        df_real = pd.pivot_table(cashflows, values='amount', index=['actual_pay_dt'], aggfunc="sum")
        data = self._generate_json_format(df_contractual,df_real)

        # data = {
        #     "daily": {
        #         "datasets": [{"data": [10, 80, 30, 80, 20, 60, 70], "label": "应收账款"},
        #                      {"data": [8, 70, 34, 11, 90, 66, 71], "label": "实收账款"}],
        #         "labels": ['January', 'February', 'March', 'April', 'May', 'June', 'July']},  # x-axis
        # }

        return data


    def run(self):
        order_summary_df = self.get_order_summary()
        cashflows = self.get_cashflows()
        client_infos = self.get_client_info()

        phone_nums = self.get_total_phone_by_date(order_summary_df)
        ar_list = self.get_total_ar(cashflows, client_infos)
        today_cash = self.get_cash_by_date(cashflows, client_infos, self.today)
        tomorrow_cash = self.get_cash_by_date(cashflows, client_infos, self.tomorrow)
        default_num = self.get_default_num(cashflows)
        invest = self.total_capital - self.balance
        profit = (ar_list[0] - invest) / invest
        data = {
            'segment': 'index',
            'total_phone': "{:,}".format(phone_nums[0]),
            'phone_num_dod': "{:,}".format(phone_nums[0] - phone_nums[1]),
            'phone_num_wtd': "{:,}".format(phone_nums[0] - phone_nums[2]),
            'total_capital': "{:,}".format(self.total_capital),
            'balance': "{:,}".format(self.balance),
            'total_ar': "{:,}".format(ar_list[0]),
            'ar_dod': "{:,}".format(ar_list[0] - ar_list[1]),
            'ar_wtd': "{:,}".format(ar_list[0] - ar_list[2]),
            'today_cash': "{:,}".format(today_cash),
            'tomorrow_cash': "{:,}".format(tomorrow_cash),
            'profit': "{:.1f}%".format(profit * 100),
            'default_num': default_num
        }
        return data
