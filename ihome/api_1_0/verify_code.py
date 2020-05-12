# coding:utf-8

# 导入蓝图对象，以便能够使用视图
from . import api
from flask import current_app, jsonify, make_response, request
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants, db
from ihome.utils.response_code import RET
from ihome.models import User

from ihome.libs.yuntongxun.send_sms import CCP
import random

# from ihome.tasks.tasks_sms import send_sms
from ihome.tasks.sms.tasks import send_sms


@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id:
    :return: 正常 > 图片，异常 > jason代码
    """
    # 获取参数 - 视图传递
    # 校验参数 - 视图校验
    # 业务逻辑处理
    # > 生产图片验证码相关内容
    name, text, image_data = captcha.generate_captcha()
    # > 保存到redis数据库
    try:
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志文件
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存数据库image code id错误")

    # 返回值
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# # GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
# @api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
# def get_sms_code(mobile):
#     """获取短信验证码"""
#     # 获取参数
#     image_code = request.args.get("image_code")
#     image_code_id = request.args.get("image_code_id")
#
#     # 校验参数
#     if not all([image_code_id, image_code]):
#         # 表示参数不完整
#         return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
#
#     # 业务逻辑处理
#     # 从redis中取真实的图片验证码
#     try:
#         db_image_code = redis_store.get("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="redis数据库错误")
#
#     # 判断验证码是否过期
#     if db_image_code is None:
#         # 数据库中不存在，图片验证码失效
#         return jsonify(errno=RET.DBERR, errmsg="图片验证码失效")
#
#     # 删除redis中的图片验证码，防止用户使用同一图片验证码多次验证
#     try:
#         redis_store.delete("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     # 与用户填写的值进行对比
#     if image_code.lower() != db_image_code.lower():
#         # 数据不相等，填写错误
#         return jsonify(errno=RET.PARAMERR, errmsg="验证码填写错误")
#
#     # 判断对这个手机号的操作，在60秒内有没有之前的记录
#     try:
#         send_flag = redis_store.get("send_sms_code_%s" % mobile)
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if send_flag is not None:
#             # 表示60秒内有发送过记录
#             return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后重试")
#
#     # 判断手机号是否存在
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user is not None:
#             # 手机号已经存在
#             return jsonify(errno=RET.DATAEXIST, errmsg="手机号已经存在，无需再注册")
#
#     # 如果手机号不存在，则生成短信验证码
#     sms_code = "%06d" % random.randint(0, 999999)
#
#     # 保存真实的短信验证码
#     try:
#         db_sms_code = redis_store.setex("sms_codes_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
#
#         # 保存发送给这个手机号的记录，防止用户在60秒内再次发送短信操作
#         redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
#
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="保存短信验证码错误")
#
#     # 发送短信
#     try:
#         ccp = CCP()
#         resp = ccp.send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.THIRDERR, errmsg="第三方发送短信异常")
#
#     # 返回应答
#     if resp == 0:
#         return jsonify(errno=RET.OK, errmsg="发送成功")
#     else:
#         return jsonify(errno=RET.THIRDERR, errmsg="发送错误")


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""
    # 获取参数
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")

    # 校验参数
    if not all([image_code_id, image_code]):
        # 表示参数不完整
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 业务逻辑处理
    # 从redis中取真实的图片验证码
    try:
        db_image_code = redis_store.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库错误")

    # 判断验证码是否过期
    if db_image_code is None:
        # 数据库中不存在，图片验证码失效
        return jsonify(errno=RET.DBERR, errmsg="图片验证码失效")

    # 删除redis中的图片验证码，防止用户使用同一图片验证码多次验证
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 与用户填写的值进行对比
    if image_code.lower() != db_image_code.lower():
        # 数据不相等，填写错误
        return jsonify(errno=RET.PARAMERR, errmsg="验证码填写错误")

    # 判断对这个手机号的操作，在60秒内有没有之前的记录
    try:
        send_flag = redis_store.get("send_sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示60秒内有发送过记录
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后重试")

    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 手机号已经存在
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号已经存在，无需再注册")

    # 如果手机号不存在，则生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存真实的短信验证码
    try:
        db_sms_code = redis_store.setex("sms_codes_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 保存发送给这个手机号的记录，防止用户在60秒内再次发送短信操作
        redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码错误")

    # 发送短信
    # 使用celery异步发送短信, delay函数调用后立即返回
    # send_sms.delay(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)
    send_sms.delay(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)

    # 返回应答
    # 发送成功
    return jsonify(errno=RET.THIRDERR, errmsg="发送错误")
