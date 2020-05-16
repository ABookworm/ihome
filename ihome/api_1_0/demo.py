# coding:utf-8

from . import api
from ihome import db, models
from flask import current_app, request


@api.route("/index")
def index():
    # 测试logs
    # current_app.logger.error("error info")
    # current_app.logger.warn("warn info")
    # current_app.logger.info("info info")
    current_app.logger.dubug("debug info")
    return "index page"