# coding: utf-8

from qiniu import Auth, put_data, etag
import qiniu.config

# 需要填写你的 Access Key 和 Secret Key
access_key = 'GqyBxsg7NqVmDlT2gVp17j4FsGX_4PRnPHbNFbAa'
secret_key = '6VL3T9FvPq-fNu0LN2_VAGZ6CqulHG2lOrlsy1Na'


def storage(file_data):
    """
    上传文件到七牛云
    :param file_data: 要上传的数据
    :return:
    """
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'ihome20191101'

    # 上传后保存的文件名, 本程序不使用
    # key = 'my-python-logo.png'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    # 要上传文件的本地路径
    # localfile = './sync/bbb.jpg'

    # token, name,
    ret, info = put_data(token, None, file_data)
    # print(info)
    # print("*"*100)
    # print(ret)
    if info.status_code == 200:
        # 表示上传成功，返回name
        return ret.get("key")
    else:
        raise Exception("图片上传七牛云服务失败")


# coding for the test.
# if __name__ == "__main__":
#     with open("./1.png", "rb") as f:
#         file_data = f.read()
#         storage(file_data)
