# coding=utf-8

from CCPRestSDK import REST

# 主帐号
accountSid= '8aaf07086e0115bb016e0782f01302ee'

# 主帐号Token
accountToken= 'e1cada12882a4a909c70b40a6a92d1ba'

# 应用Id
appId='8aaf07086e0115bb016e0782f07802f5'

# 请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com'

# 请求端口
serverPort='8883'

# REST版本号
softVersion='2013-12-26'

# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# @param $tempId 模板Id


class CCP(object):
    """自己封装的辅助类"""
    # 创建保存对象的类属性
    instance = None

    def __new__(cls):
        # 单例模式
        # 判断CPP类有没有已经创建好的对象，如果没有创建，并保存
        if cls.instance is None:
            obj = super(CCP, cls).__new__(cls)
            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)
            cls.instance = obj
        # 如果有则将保存的对象返回
        return cls.instance

    def send_template_sms(self, to, datas, temp_id):
        """
        发送短信验证码
        :param to: 发送给谁
        :param datas:  发送内容, 以字典形式传输参数
        :param temp_id:  云通讯模板定义ID： 测试为1
        :return:  发送成功：0， 失败为：1
        """
        result = self.rest.sendTemplateSMS(to, datas, temp_id)
        # for k, v in result.iteritems():
        #     if k == 'templateSMS':
        #         for k, s in v.iteritems():
        #             print('%s:%s' % (k, s))
        #     else:
        #         print('%s:%s' % (k, v))
        # send sm format:
        # smsMessageSid:6
        # ec559118ca441dd90b1cc072f5af93d
        # dateCreated:20191026191835
        # statusCode:000000
        status_code = result.get("statusCode")
        if status_code == "000000":
            return 0
        else:
            return -1


if __name__ == "__main__":
    cpp = CCP()
    resp = cpp.send_template_sms("15626950790", ["1234", "5"], 1)
    print(resp)