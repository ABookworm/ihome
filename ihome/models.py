# coding:utf-8
from ihome import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ihome import constants


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class User(BaseModel, db.Model):
    """用户模型类"""
    __tablename__ = "ih_user_profile"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    mobile = db.Column(db.String(11), unique=True, nullable=False)

    # 用户认证真实信息
    real_name = db.Column(db.String(32))
    id_card = db.Column(db.String(20))

    avatar_url = db.Column(db.String(128))  # 用户头像地址

    houses = db.relationship("House", backref="user")
    orders = db.relationship("Order", backref="user")

    # 加上property装饰器，将方法变为属性
    @property
    def password(self):
        """读取属性的函数行为"""
        # 这个属性只能设置，不能读写
        raise AttributeError

    @password.setter
    def password(self, password):
        """
        对密码进行设置
        :param: the origin password
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, passwd):
        """
        检验密码的正确性
        :param passwd: 用户登录填写的原始密码
        :return:
        """
        return check_password_hash(self.password_hash, passwd)

    def to_dict(self):
        """将用户对象转换为字典数据"""
        user_dict = {
            "user_id": self.id,
            "name": self.name,
            "mobile": self.mobile,
            "avatar": constants.QINIU_URL_DOMAIN + self.avatar_url if self.avatar_url else "",
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return user_dict

    def auth_to_dict(self):
        """将实名信息转换为字典数据"""
        auth_dict = {
            "user_id": self.id,
            "real_name": self.real_name,
            "id_card": self.id_card
        }
        return auth_dict


class Area(BaseModel, db.Model):
    """城区模型类"""
    __tablename__ = "ih_area_info"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    house = db.relationship("House", backref="area")

    def to_dict(self):
        """将对象转换为字典"""
        d = {
            "aid": self.id,
            "aname": self.name
        }
        return d


# 房屋设施表，建立房屋与设施的多对多关系
house_facility = db.Table(
    # 表名称
    "ih_house_facility",
    # 房屋编号
    db.Column("house_id", db.Integer, db.ForeignKey("ih_house_info.id"), primary_key=True),
    # 设施编号
    db.Column("facility_id", db.Integer, db.ForeignKey("ih_facility_info.id"), primary_key=True)
)


class House(BaseModel, db.Model):
    """房屋信息模型类"""
    __tablename__ = "ih_house_info"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user_profile.id"), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey("ih_area_info.id"), nullable=False)

    title = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Integer, default=0)  # 单价，单位：分/晚
    address = db.Column(db.String(512), default="")
    index_image_url = db.Column(db.String(256), default="")

    deposit = db.Column(db.Integer, default=0)  # 入住押金

    room_count = db.Column(db.Integer, default=1)  # 房间数目
    acreage = db.Column(db.Integer, default=0)  # 房屋面积
    unite = db.Column(db.String(32), default="")  # 房屋单元，如几室几厅
    capacity = db.Column(db.Integer, default=1)  # 房屋容纳人数
    beds = db.Column(db.String(64), default="")  # 房屋床铺配置

    min_days = db.Column(db.Integer, default=1)  # 最少入住天数，默认一晚
    max_days = db.Column(db.Integer, default=0)  # 最多入住天数，0表示无限制

    order_count = db.Column(db.Integer, default=0)  # 房屋已完成订单总数
    order = db.relationship("Order", backref="house")  # 房屋的订单情况

    images = db.relationship("HouseImage")  # 房屋的所有图片
    facilities = db.relationship("Facility", secondary = house_facility)  # 房屋的设施

    def to_basic_dict(self):
        """将对象转换为字典"""
        house_dict = {
            "house_id": self.id,
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "area_name": self.area.name,
            "image_url": constants.QINIU_URL_DOMAIN + self.index_image_url if self.index_image_url else "",
            "room_count": self.room_count,
            "order_count": self.order_count,
            "user_avatar": constants.QINIU_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "creat_time": self.create_time.strftime("%Y-%m-%d")
        }
        return house_dict

    def to_full_dict(self):
        """将对象转换为字典"""
        house_dict = {
            "hid": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name,
            "user_avatar": constants.QINIU_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "deposit": self.deposit,
            "room_count": self.room_count,
            "acreage": self.acreage,
            "unit": self.unite,
            "capacity": self.capacity,
            "beds": self.beds,

            "min_days": self.min_days,
            "max_days": self.max_days
        }

        # 房屋图片处理
        img_urls = []
        for image in self.images:
            img_urls.append(constants.QINIU_URL_DOMAIN + img_url)
        house_dict["img_urls"] = img_urls

        # 房屋设施处理
        facilities = []
        for facility in self.facilities:
            facilities.append(facility.id)
        house_dict["facilities"] = facilities

        # 评论信息处理
        comments = []
        orders = Order.query.filter(Order.house_id == self.id, Order.status == "COMPLETE", Order.comment != None).\
            order_by(Order.updata_time.desc()).limit(constants.HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS)
        for order in orders:
            comment = {
                "comment": order.comment,  # 获取评论
                "user_name": order.user.name if order.user.name != order.user.name else "匿名用户",  # 设置用户手机号码隐私
                "ctime": order.update_time.strftime("%Y-%m-%d %H:%M:%S")  # 设置时间格式
            }
            comments.append(comment)
        house_dict["comments"] = comments

        return house_dict


class Facility(BaseModel, db.Model):
    """房屋设施信息"""
    __tablename__ = "ih_facility_info"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)


class HouseImage(BaseModel, db.Model):
    """房屋图片模型类"""
    __tablename__ = "ih_house_image"

    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey("ih_house_info.id"), nullable=False)
    url = db.Column(db.String(256), nullable=False)  # 所有图片路径地址


class Order(BaseModel, db.Model):
    """订单详情模型类"""
    __tablename__ = "ih_order_info"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user_profile.id"), nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey("ih_house_info.id"), nullable=False)

    begin_date = db.Column(db.DateTime, nullable=False)
    end_data = db.Column(db.DateTime, nullable=False)
    days = db.Column(db.Integer, nullable=False)  # 总预订天数

    house_price = db.Column(db.Integer, nullable=False)  # 房屋单价
    amount = db.Column(db.Integer, nullable=False)  # 订单总金额

    # 订单状态: 默认待接单
    status = db.Column(
        db.Enum(
            "WAIT_ACCEPT",  # 待接单
            "WAIT_PAYMENT",  # 待支付
            "PAID",  # 已支付
            "WAIT_COMMENT",  # 待评价
            "COMPLETE",  # 已完成
            "CANCELED",  # 已取消
            "REJECTED"  # 已拒单
        ),
        default="WAIT_ACCEPT",
        index=True
    )

    comment = db.Column(db.Text)  # 订单评论信息或者拒单原因