# coding:utf-8

from celery import Celery
from ihome.libs.yuntongxun.send_sms import CCP


# 发布celery对象
celery_app = Celery("ihome", broker="redis://192.168.3.9:6379/1")


@celery_app.task
def send_sms(to, datas, temp):
    """发送短信的异步任务"""
    ccp = CCP()
    ccp.send_template_sms(to, datas, temp)