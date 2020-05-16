from . import api
from ihome.utils.commons import login_required
from ihome.models import Order
from flask import g, current_app, jsonify, request
from ihome.utils.response_code import RET
from alipay import Alipay
from ihome import constants, db
import os


# ToDo: 支付接口开发
def order_pay(order_id):
    """发起支付宝支付"""
    user_id = g.user_id

    # 判断订单状态
    try:
        order = Order.query.filter(Order.id==order_id, Order.)

    
