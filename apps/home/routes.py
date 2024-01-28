# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from dateutil.relativedelta import relativedelta

from apps.home import blueprint
from apps.home.order_analytics import OrderAnalytics
from apps.home.models import OrderSummary, ClientInfo, Cashflow
from sqlalchemy import text
from flask import render_template, redirect, request, url_for
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps import db
import pandas as pd
import logging
import datetime
import math

log = logging.getLogger(__name__)


@blueprint.route('/index')
@login_required
def index():
    analytics = OrderAnalytics()
    data = analytics.run()
    data['segment'] = 'index'

    return render_template('home/index.html', **data)


def get_pay_dates(order_dt, term):
    res = [order_dt]
    next_dt = order_dt
    for i in range(term - 1):
        next_dt = next_dt + relativedelta(months=1)
        res.append(next_dt)

    return res


def create_orders_based_summary(df):
    """
    Only insert when there is a new records
    :param orders_summary:
    :return:
    """
    today = datetime.date.today()

    cashflow_list = []
    client_info = pd.DataFrame(
        columns=['order_id', 'order_dt', 'maturity_dt', 'term', 'tenor', 'official_px', 'buydown', 'deposit'])
    pay_cols = ['pay' + str(x) for x in range(1, 13)]
    for i, row in df.iterrows():
        cf_df = pd.DataFrame(columns=['order_id', 'seq', 'amount', 'due_dt', 'actual_pay_dt'])
        order_id = row['order_id']
        if isinstance(row['order_time'], datetime.datetime):
            order_dt = row['order_time'].date()
        else:
            order_dt = datetime.datetime.strptime(row['order_time'].replace('\n',''), '%Y-%m-%d %H:%M:%S').date()
        official_px = row['official_px']
        buydown = row['buydown']
        deposit = row['deposit']

        term = 6 if math.isnan(row['pay12']) else 12
        pay_dates = get_pay_dates(order_dt, term)
        tenor = len([d for d in pay_dates if d> today])
        maturity_dt = pay_dates[-1]
        client_info.loc[len(client_info)] = [order_id, order_dt, maturity_dt, term, tenor, official_px, buydown, deposit]

        for j, due_dt in enumerate(pay_dates):
            cf_df.loc[j] = [order_id, j + 1, row[pay_cols[j]], due_dt, due_dt if due_dt <= today else None]

        cashflow_list.append(cf_df)

    final_cashflows = pd.concat(cashflow_list)

    return client_info, final_cashflows


def get_new_orders_summary(new_df):
    old_df = OrderAnalytics().order_summary_df
    if not old_df.empty:
        old_keys = old_df['order_id'].unique().tolist()
        new_keys = new_df['order_id'].unique().tolist()
        diff_keys = list(set(old_keys).symmetric_difference(set(new_keys)))
        res = new_df.loc[new_df['order_id'].isin(diff_keys)]
        return res
    else:
        return new_df


def insert_client_info(df):
    # ['order_id', 'order_dt', 'maturity_dt', 'term', 'tenor', 'official_px', 'buydown', 'deposit']
    try:

        for _, row in df.iterrows():
            new_record = ClientInfo(order_id=row['order_id'], order_dt=row['order_dt'],
                                    maturity_dt=row['maturity_dt'], term=row['term'], tenor=row['tenor'],
                                    official_px=row['official_px'], buydown=row['buydown'],
                                    deposit=row['deposit'])
            db.session.add(new_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.exception(str(e))


def insert_cashflow(df):
    # ['order_id', 'seq','amount','due_dt','actual_pay_dt']
    try:
        i=1
        for _, row in df.iterrows():
            new_record = Cashflow(id=i, order_id=row['order_id'], seq=row['seq'],
                                  amount=row['amount'], due_dt=row['due_dt'], actual_pay_dt=row['actual_pay_dt'])
            i+=1
            db.session.add(new_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.exception(str(e))


@blueprint.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'excel_file' not in request.files:
        return 'No file part'
    file = request.files['excel_file']
    if file.filename == '':
        return 'No selected file'
    if file:
        if 'summary' in file.filename.lower():
            new_df = pd.read_excel(file)
            new_cols = {'序号':'id','订单号':'order_id','姓名':'name','下单时间':'order_time','设备信息':'device','采购价':'purchase_px',
                            '官网售价':'official_px','第1期':'pay1','第2期':'pay2','第3期':'pay3','第4期':'pay4','第5期':'pay5',
                            '第6期':'pay6','第7期':'pay7','第8期':'pay8','第9期':'pay9','第10期':'pay10','第11期':'pay11','第12期':'pay12',
                            '押金':'deposit','买断':'buydown'}
            new_df = new_df.rename(columns=new_cols)


            insert_df = get_new_orders_summary(new_df)

            if not insert_df.empty:
                try:
                    client_info, final_cashflows = create_orders_based_summary(insert_df)
                    insert_client_info(client_info)
                    insert_cashflow(final_cashflows)
                    # Insert summary table
                    for _, row in insert_df.iterrows():
                        new_record = OrderSummary(id=row['id'], order_id=row['order_id'], name=row['name'],
                                                  order_time=row['order_time'], device=row['device'],
                                                  purchase_px=row['purchase_px'],
                                                  official_px=row['official_px'], pay1=row['pay1'],
                                                  pay2=row['pay2'], pay3=row['pay3'], pay4=row['pay4'],
                                                  pay5=row['pay5'], pay6=row['pay6'], pay7=row['pay7'],
                                                  pay8=row['pay8'], pay9=row['pay9'],
                                                  pay10=row['pay10'], pay11=row['pay11'], pay12=row['pay12'],
                                                  deposit=row['deposit'], buydown=row['buydown'])
                        db.session.add(new_record)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    log.exception(str(e))

        return redirect(url_for('home_blueprint.index'))  # 上传成功后重定向到首页
    return 'Error'


@blueprint.route('/update_data', methods=['POST'])
@login_required
def update_data():
    if 'excel_file' not in request.files:
        return 'No file part'
    file = request.files['excel_file']
    if file.filename == '':
        return 'No selected file'
    if file:
        df = pd.read_excel(file)  # 使用Pandas读取Excel文件
        try:
            for _, row in df.iterrows():
                new_record = OrderSummary(id=row['序号'], order_id=row['订单号'], name=row['姓名'],
                                          order_time=row['下单时间'], device=row['设备信息'], purchase_px=row['采购价'],
                                          official_px=row['官网售价'], pay1=row['第1期'],
                                          pay2=row['第2期'], pay3=row['第3期'], pay4=row['第4期'],
                                          pay5=row['第5期'], pay6=row['第6期'], pay7=row['第7期'],
                                          pay8=row['第8期'], pay9=row['第9期'],
                                          pay10=row['第10期'], pay11=row['第11期'], pay12=row['第12期'],
                                          deposit=row['押金'], buydown=row['买断'])
                db.session.add(new_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.exception(str(e))

        return redirect(url_for('home_blueprint.index'))  # 上传成功后重定向到首页
    return 'Error'


@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):
    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
