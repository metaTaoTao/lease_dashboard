# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from apps.home.order_analytics import OrderAnalytics
from apps.home.models import OrderSummary
from sqlalchemy import text
from flask import render_template, redirect, request, url_for
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps import db
import pandas as pd
import logging
log = logging.getLogger(__name__)

@blueprint.route('/index')
@login_required
def index():
    analytics = OrderAnalytics()
    data = analytics.run()
    data['segment'] = 'index'

    return render_template('home/index.html', **data)

def get_total_phone():
    sql_query = text("select count(*) from OrderSummary") # to avoid SQL attack
    result = db.engine.execute(sql_query)

    # 获取查询结果
    total_phone = result.scalar()
    return total_phone

@blueprint.route('/upload', methods=['POST'])
@login_required
def upload_file():
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
