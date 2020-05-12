# coding:utf-8

from . import api
from ihome import redis_store
from ihome.utils.commons import login_required
from flask import g, current_app, jsonify, request, session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import Area, House, Facility, HouseImage, User, Order
from ihome import db, constants
import json
from datetime import datetime

@api.route("/orders", methods=["POST"])
@login_required
def save_order():
    """保存订单"""
    user_id = g.user_id

    # 获取参数
    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")