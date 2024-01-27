from sqlalchemy import text
from apps import db


class OrderAnalytics:
    def __init__(self):
        self.total_capital = 6500000

    def get_total_phone(self):
        sql_query = text("select count(*) from OrderSummary")  # to avoid SQL attack
        result = db.engine.execute(sql_query)

        # 获取查询结果
        total_phone = result.scalar()
        return total_phone

    def run(self):
        total_phone = self.get_total_phone()
        data = {
            'segment': 'index',
            'total_phone': total_phone,
            'total_capital':self.total_capital
        }
        return data
