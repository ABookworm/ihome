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


area_li = None
@api.route("/areas")
def get_area_info():
    """城区信息"""
    # 首先尝试从redis中读取数据
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # redis有缓存数据
            current_app.logger.info("hit redis area_info")
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库，读取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    area_dict_li = []
    # 将对象装换为字典
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # 数据处理：将数据转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis中
    try:
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """保存房屋的基本信息"""
    user_id = g.user_id

    # 获取房屋信息
    # 前端发送过来的json数据
    # {
    #     "title": "",
    #     "price": "",
    #     ""
    # }
    house_dict = request.get_json()

    title = house_dict.get("title")
    price = house_dict.get("price")
    area_id = house_dict.get("area_id")
    address = house_dict.get("address")
    room_count = house_dict.get("room_count")
    acreage = house_dict.get("acreage")
    unit = house_dict.get("unit")
    capacity = house_dict.get("capacity")
    beds = house_dict.get("beds")
    deposit = house_dict.get("deposit")
    min_days = house_dict.get("min_days")
    max_days = house_dict.get("max_days")

    # 校验参数完整性
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, max_days, min_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断金额是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验城区是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    # 保存数据
    house = House(
        user_id = user_id,
        area_id = area_id,
        title = title,
        price = price,
        address = address,
        room_count = room_count,
        acreage = acreage,
        unite = unit,
        capacity = capacity,
        beds = beds,
        deposit = deposit,
        min_days = min_days,
        max_days = max_days
    )

    # 处理房屋设施信息.1:5000/api/v1.0/houses/image
    facility_ids = house_dict.get("facility")

    # 如果用户勾选了设施信息，再保存信息
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库错误")

        if facilities:
            house.facilities = facilities

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 保存成功，返回
    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """保存房屋的图片"""
    image_file = request.files.get("house_image")
    house_id = request.form.get("house_id")

    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 保存图片到七牛云
    image_data = image_file.read()
    try:
        file_name= storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="第三方服务错误")

    # 保存图片信息到数据库
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    # 保存房屋的主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据库异常")

    image_url = constants.QINIU_URL_DOMAIN + file_name

    return jsonify(errno=RET.OK, errmsg="OK", data={"image_url": image_url})


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    """获取房东发布的房源信息条目"""
    user_id = g.user_id

    try:
        user = User.query.filter_by(user_id=user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    # 将查询的房屋信息转换为字典存放在列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋信息"""
    # 从redis缓存中获取数据
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        current_app.logger.info("Hit house index info on redis")
        # 因为redis中缓存的为json字符串，所有直接进行字符串拼接返回
        return '{"errno": 0, "errmsg": "OK", "data": %s}' % ret, 200, {"Content-Type": "application/josn"}
    else:
        # 从数据库中获取数据,返回房屋订单数目最多的五条数据
        try:
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")

        houses_list = []
        for house in houses:
            # 判断未设置主页图片的房屋跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json数据，缓存到redis中
        json_house = json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_house)
        except Exception as e:
            current_app.logger.error(e)

        return '{"errno":0, "errmsg": "OK", "data": %s}' % json_house, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端需要依据用户是否为房东来决定是否显示预订按钮，所以需要获取登录用户的user_id
    # 尝试获取用户登录信息，未登录时返回user_id = -1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数缺失")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        current_app.logger.info("hit house info from redis")
        resp_data = '{"errno": "0", "errmsg": "OK", "data": {"user_id": %s, "house": %s}}' % (user_id, ret)
        return resp_data, 200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典数据
    # Todo: to_full_dict()
    try:
        house_dict = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    house_json = json.dumps(house_dict)

    # 存入到redis缓存
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRES, house_json)
    except Exception as e:
        current_app.logger.error(e)

    # 组织数据，返回
    resp_data = '{"errno": "0", "errmsg": "OK", "data": {"user_id":%s, "house":%s}}' % (user_id, house_json)
    return resp_data, 200, {"Content-Type": "application/json"}


# GET /api/v1.0/houses?sd=2017-12-01&ed=2017-12-31&aid=10&sk=new&p=1
@api.route("/houses")
def get_house_list():
    """获取房屋的列表信息(搜索页面）"""
    # 获取参数
    start_date = request.args.get("sd")
    end_date = request.args.get("ed")
    area_id = request.args.get("aid")
    sort_key = request.args.get("sk", "new")
    page = request.args.get("p")

    # 处理时间
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数有误")

    # 判断区域ID
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            return jsonify(errno=RET.PARAMERR, errmsg="区域信息有误")

    # 排序关键字， 无关紧要，可以通过默认设置进行
    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 首先尝试获取缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库
    # 过滤条件的参数容器
    filter_params = []

    # 填充过滤参数
    # > 处理时间条件
    conflict_orders = None

    try:
        if start_date and end_date:
            # 查询冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_data >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_data >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if conflict_orders:
        # 从订单中获取冲突的房屋ID
        conflict_house_ids = [conflict_order.house_id for conflict_order in conflict_orders]
        # 如果冲突的房屋id不为空，向查询参数中添加条件
        if conflict_orders:
            filter_params.append(House.id.notin_(conflict_house_ids))

    # > 处理区域条件
    if area_id:
        filter_params.append(House.area_id == area_id)

    # 查询数据库
    # > 补充排序条件
    if sort_key == "booking":
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_params).order_by(House.priceq.asc())
    elif sort_key == "price-des":
        house_query = House.query.filter(*filter_params).order_by(House.priceq.desc())
    else:  # 默认按照新旧排序
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 处理分页条件
    try:
        # paginate() params: 当前页数，每页数量，默认错误输出方法
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 获取页面数据 page_obj.itmes
    houses = []
    for house in page_obj.items:
        houses.append(house.to_basic_dict())

    # 获取总页数
    total_pages = page_obj.pages

    resp_dict = dict(errno=RET.OK, errmsg="OK", data={"total_page": total_pages, "houses": houses, "current_page": page})
    resp_json = json.dumps(resp_dict)

    if page <= total_pages:
        # 设置缓存
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
        try:
            # 设置哈希类型缓存数据
            redis_store.hset(redis_key, page, resp_json)
            redis_store.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)
        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}