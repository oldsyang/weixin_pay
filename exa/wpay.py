# -*- coding: utf-8 -*-
# @Author  : oldsyang

import string
import random
import time
import hashlib
import urllib2
from django.conf import settings
import requests
import copy
import json

try:
    from xml.etree import cElementTree as ETree
except ImportError:
    from xml.etree import ElementTree as ETree


class WeixinException(Exception):
    def __init__(self, msg):
        super(WeixinException, self).__init__(msg)


class MxPay(object):
    def __init__(self):
        '''
        
        Args:
        '''

        if not settings.APP_ID:
            raise WeixinException("缺少接口必填参数app_id")
        if not settings.MCH_ID:
            raise WeixinException("缺少接口必填参数mch_id")
        if not settings.WX_MCH_KEY:
            raise WeixinException("缺少接口必填参数wx_mch_key")

        self.APP_ID = settings.APP_ID
        self.MCH_ID = settings.MCH_ID
        self.WX_MCH_KEY = settings.WX_MCH_KEY

        self.NOTIFY_URL = settings.ASYN_NOTIFY_URL
        self.ORDER_URL = settings.ORDER_URL
        self.SEARCH_URL = settings.SEARCH_URL
        self.CLOSE_URL = settings.CLOSE_URL
        self.REFUND_URL = settings.REFUND_URL
        self.SEARCH_REFUND_URL = settings.SEARCH_REFUND_URL

        self.API_CLIENT_CERT_PATH = settings.API_CLIENT_CERT_PATH
        self.API_CLIENT_KEY_PATH = settings.API_CLIENT_KEY_PATH

    @staticmethod
    def get_nonce_str(length=32):
        '''
        
        Args:
            length(int): 随机数的长度

        Returns:
            返回length长度的随机字符串

        '''
        char = string.ascii_letters + string.digits
        return "".join(random.choice(char) for _ in range(length))

    def get_xml(self, params, is_compatible=False):
        # 拼接参数的xml字符串
        request_xml_str = '<xml>'
        for key, value in params.items():
            if not is_compatible and not value: continue
            if isinstance(value, basestring):
                request_xml_str = '%s<%s><![CDATA[%s]]></%s>' % (request_xml_str, key, value, key,)
            else:
                request_xml_str = '%s<%s>%s</%s>' % (request_xml_str, key, value, key,)
        request_xml_str = '%s</xml>' % request_xml_str

        return request_xml_str

    @staticmethod
    def sign(params, key, is_compatible=False):
        '''
            生成签名
            参考微信签名生成算法：https://pay.weixin.qq.com/wiki/doc/api/native.php?chapter=4_3
        Args:
            params(dict): 数据字典
            key(str): 签名的key
            is_compatible(bool): 是否兼容模式，对字典里value为空的数据也要签名

        Returns:

        '''

        raw = [(k, str(params[k]) if isinstance(params[k], (int, float)) else params[k]) for k in sorted(params.keys())]
        print("raw:", raw)
        if is_compatible:
            s = "&".join("=".join(kv) for kv in raw)
        else:
            s = "&".join("=".join(kv) for kv in raw if kv[1])
        print("s:", s)
        s += "&key={0}".format(key)
        return hashlib.md5(s.encode("utf-8") if isinstance(s, unicode) else s).hexdigest().upper()

    @staticmethod
    def check(params, private_key):
        '''
        验证签名是否正确
        Args:
            params: 字典数据 
            private_key: 验证的key

        Returns:

        '''
        tmp_params = copy.deepcopy(params)
        sign = tmp_params.pop("sign")
        return sign == MxPay.sign(tmp_params, private_key)

    @staticmethod
    def get_time_stamp():
        '''
        
        Returns: 返回时间戳

        '''
        return str(time.time()).split(".", 1)[0]

    def option_request(self, url, xml_str, with_ca=False):
        '''
        发送https请求，也可以带证书
        Args:
            url(str): 请求地址
            xml_str(str): 格式为xml类型的字符串
            with_ca: 是否带证书

        Returns:
            返回字典形式的请求响应内容

        '''
        # res = requests.post(self.ORDER_URL, data=json.dumps(xml_str, ensure_ascii=False),
        #                     headers={'Connection': 'close'}, verify=False)
        # res_content = self.to_dict(res.content)

        if with_ca:
            res = requests.post(url, data=json.dumps(xml_str, ensure_ascii=False),
                                cert=(self.API_CLIENT_CERT_PATH, self.API_CLIENT_KEY_PATH))
            res_content_dict = self.to_dict(res.content)
        else:
            res = urllib2.Request(url, data=json.dumps(xml_str, ensure_ascii=False))
            try:
                resp = urllib2.build_opener(urllib2.HTTPSHandler()).open(res, timeout=20)
            except urllib2.HTTPError, e:
                resp = e
            res_content_dict = self.to_dict(resp.read())

        # 这里可以直接返回res_content_dict，交由具体的view去处理（一定要做做签名验证），下面的代码仅作代码调式
        if res_content_dict.get("return_code") == "SUCCESS":
            # 说明有正常返回
            if res_content_dict.get("result_code", None) == "SUCCESS":
                if self.check(res_content_dict, self.WX_MCH_KEY):
                    return res_content_dict
            else:
                print("{0}:{1}".format(res_content_dict.get("err_code"), res_content_dict.get("err_code_des").encode("utf-8")))
        else:
            # 类似于appid,mch_id等有错误
            print("return_msg:%s" % res_content_dict.get("return_msg").encode("utf-8"))

        return res_content_dict

    def create_order(self, **kwargs):
        '''
        统一下单
        Args:
            trade_type(str): 交易类型,JSAPI--公众号支付、NATIVE--原生扫码支付、APP--app支付，统一下单接口trade_type的传参可参考这里MICROPAY--刷卡支付，刷卡支付有单独的支付接口，不调用统一下单接口
            total_fee(int): 交易金额默认为人民币交易，接口中参数支付金额单位为【分】，参数值不能带小数。对账单中的交易金额单位为【元】。外币交易的支付金额精确到币种的最小单位，参数值不能带小数点
            spbill_create_ip(str): APP和网页支付提交用户端ip，Native支付填调用微信支付API的机器IP。
            out_trade_no(str): 商户系统内部订单号，要求32个字符内，只能是数字、大小写字母_-|*@ ，且在同一个商户号下唯一。详见商户订单号
            body(str): 商品简单描述，该字段请按照规范传递，具体请见参数规定
            product_id: trade_type=NATIVE时（即扫码支付），此参数必传。此参数为二维码中包含的商品ID，商户自行定义。

        Returns:
            返回二维码的content

        '''

        if "out_trade_no" not in kwargs:
            raise WeixinException("缺少统一支付接口必填参数out_trade_no")
        if "body" not in kwargs:
            raise WeixinException("缺少统一支付接口必填参数body")
        if "total_fee" not in kwargs:
            raise WeixinException("缺少统一支付接口必填参数total_fee")
        if "trade_type" not in kwargs:
            raise WeixinException("缺少统一支付接口必填参数trade_type")
        if "trade_type" not in kwargs:
            raise WeixinException("trade_type为NATIVE时，product_id为必填参数")
        if kwargs["trade_type"] == "NATIVE" and "product_id" not in kwargs:
            raise WeixinException(u"trade_type为NATIVE时，product_id为必填参数")

        if not self.NOTIFY_URL:
            raise WeixinException("缺少统一支付接口必填参数notify_url")
        if not self.ORDER_URL:
            raise WeixinException("统一下单地址不能为空")

        params = {
            "appid": self.APP_ID,
            "mch_id": self.MCH_ID,
            "notify_url": self.NOTIFY_URL,

            "time_stamp": self.get_time_stamp(),
            "nonce_str": self.get_nonce_str(),

            "body": kwargs.get("body"),
            "out_trade_no": kwargs.get("out_trade_no"),
            "total_fee": kwargs.get("total_fee"),
            "spbill_create_ip": kwargs.get("spbill_create_ip"),
            "trade_type": kwargs.get("trade_type"),
            "product_id": kwargs.get("product_id")
        }

        res_content_dict = self.__option_params_return_dict(self.ORDER_URL, params)
        return res_content_dict, self.get_qrcode(res_content_dict, "code_url")

    def search_order(self, **kwargs):
        '''
        查询订单url：https://api.mch.weixin.qq.com/pay/orderquery
        官方文档：https://pay.weixin.qq.com/wiki/doc/api/native.php?chapter=9_2

        Args:
            transaction_id (str): 微信的订单号，建议优先使用 （在异步回调的时候会返回）
            out_trade_no(str) : 商户系统内部订单号，要求32个字符内，只能是数字、大小写字母_-|*@ ，且在同一个商户号下唯一。 详见商户订单号 
        Returns:

        '''

        if "transaction_id" not in kwargs and "out_trade_no" not in kwargs:
            raise WeixinException("缺少查询订单接口必填参数：transaction_id或者out_trade_no（二选一）")

        if not self.SEARCH_URL:
            raise WeixinException("查询订单地址不能为空")

        return self.__close_or_search_order(self.SEARCH_URL, **kwargs)

    def __option_params_return_dict(self, url, params, with_ca=False):
        '''
        
        Args:
            url: 请求的url
            params: 请求的参数
            with_ca: 是否启用证书

        Returns:

        '''
        # 签名
        sign = self.sign(params, self.WX_MCH_KEY)
        params["sign"] = sign

        # 转化为xml
        xml_str = self.get_xml(params)

        res_content_dict = self.option_request(url, xml_str, with_ca)

        # 查询订单的结果，看官方文档返回的参数去继续后面的业务
        return res_content_dict

    def __close_or_search_order(self, url, **kwargs):
        '''
        关闭或者查询订单，为了方便，查询退款也放在这里（实际上这样不利于对非必选字段的扩展）
        Args:
            url: 
            **kwargs: 

        Returns:

        '''
        params = {
            "appid": self.APP_ID,
            "mch_id": self.MCH_ID,

            "nonce_str": self.get_nonce_str(),
            "transaction_id": kwargs.get("transaction_id", ""),

            "out_trade_no": kwargs.get("out_trade_no", ""),
            "out_refund_no": kwargs.get("out_refund_no", ""),
            "refund_id": kwargs.get("refund_id", ""),
        }
        return self.__option_params_return_dict(url, params)

    def close_order(self, out_trade_no):
        '''
        关闭订单,详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_3
        Args:
            out_trade_no: 商户系统内部订单号，要求32个字符内，只能是数字、大小写字母_-|*@ ，且在同一个商户号下唯一。 

        Returns:

        '''
        if not self.CLOSE_URL:
            raise WeixinException("关闭订单地址不能为空")
        if out_trade_no:
            raise WeixinException("缺少关闭订单接口必填参数out_trade_no")

        return self.__close_or_search_order(self.CLOSE_URL, **{"out_trade_no": out_trade_no})

    def down_bills(self):
        '''
        下载对账单
        Returns:

        '''
        pass

    def refund(self, **kwargs):
        '''
        
        申请退款
        
        当交易发生之后一段时间内，由于买家或者卖家的原因需要退款时，卖家可以通过退款接口将支付款退还给买家，微信支付将在收到退款请求并且验证成功之后，按照退款规则将支付款按原路退到买家帐号上。 

        注意： 
        
        1、交易时间超过一年的订单无法提交退款 
        
        2、微信支付退款支持单笔交易分多次退款，多次退款需要提交原支付订单的商户订单号和设置不同的退款单号。申请退款总金额不能超过订单金额。 一笔退款失败后重新提交，请不要更换退款单号，请使用原商户退款单号
        
        3、请求频率限制：150qps，即每秒钟正常的申请退款请求次数不超过150次
        
            错误或无效请求频率限制：6qps，即每秒钟异常或错误的退款申请请求不超过6次
        
        4、每个支付订单的部分退款次数不能超过50次
        
        Args:
            transaction_id(str): 微信生成的订单号，在支付通知中有返回
            out_trade_no(str): 商户系统内部订单号，要求32个字符内，只能是数字、大小写字母_-|*@ ，且在同一个商户号下唯一。
            out_refund_no(str): 商户系统内部的退款单号，商户系统内部唯一，只能是数字、大小写字母_-|*@ ，同一退款单号多次请求只退一笔。
            total_fee(int): 订单总金额，单位为分，只能为整数，详见支付金额
            refund_fee(int): 退款总金额，订单总金额，单位为分，只能为整数，详见支付金额
            refund_desc(str): 若商户传入，会在下发给用户的退款消息中体现退款原因（非必填）

        Returns:

        '''

        if not self.REFUND_URL:
            raise WeixinException("申请退款地址不能为空")

        if "out_refund_no" not in kwargs:
            raise WeixinException("缺少统一支付接口必填参数out_refund_no")
        if "total_fee" not in kwargs:
            raise WeixinException("缺少统一支付接口必填参数total_fee")
        if "refund_fee" not in kwargs:
            raise WeixinException("缺少统一支付接口必填参数refund_fee")
        # if "refund_desc" not in kwargs:
        #     raise WeixinException("缺少统一支付接口必填参数refund_desc")
        if "transaction_id" not in kwargs and "out_trade_no" not in kwargs:
            raise WeixinException("缺少统一支付接口必填参数：transaction_id或者out_trade_no（二选一）")

        params = {
            "appid": self.APP_ID,
            "mch_id": self.MCH_ID,

            "nonce_str": self.get_nonce_str(),

            "out_trade_no": kwargs.get("out_trade_no"),
            "transaction_id": kwargs.get("transaction_id", ""),

            "out_refund_no": kwargs.get("out_refund_no", ""),
            "total_fee": kwargs.get("total_fee"),
            "refund_fee": kwargs.get("refund_fee"),
            # "refund_desc": kwargs.get("refund_desc"),# 此字段目前测试会报xml错误
        }
        return self.__option_params_return_dict(self.REFUND_URL, params, with_ca=True)

    def search_refund_order(self, **kwargs):
        '''
        查询退款信息
        Args:
            **kwargs: 

        Returns:

        '''
        to_str = None
        for item in ["transaction_id", "out_trade_no", "out_refund_no", "refund_id"]:
            # 只取一个
            if item in kwargs.keys():
                to_str = item
                break

        if not to_str:
            raise WeixinException("缺少查询退款接口必填参数：transaction_id或者out_trade_no或者out_trade_no或者refund_id（四选一）")

        if not self.SEARCH_REFUND_URL:
            raise WeixinException("查询退款地址不能为空")

        return self.__close_or_search_order(self.SEARCH_REFUND_URL, **kwargs)

    @staticmethod
    def get_qrcode(params, key):
        '''
        内置的生成二维码的内容，view里边可以自己做
        Args:
            params: 字典数据
            key: 二维码的key

        Returns:返回二维码图片地址

        '''
        if isinstance(params, dict):
            return params.get(key)

            # # 交易类型，取值为：JSAPI，NATIVE，APP等
            # self.trade_type = params.get("trade_type", None)
            # # 微信生成的预支付会话标识，用于后续接口调用中使用，该值有效期为2小时
            #
            # self.prepay_id = params.get("prepay_id", None)
            # # trade_type为NATIVE时有返回，用于生成二维码，展示给用户进行扫码支付(URl：weixin：//wxpay/s/An4baqw)
            # self.code_url = params.get("code_url", None)

    @staticmethod
    def to_dict(content):
        raw = {}
        root = ETree.fromstring(content)
        for child in root:
            raw[child.tag] = child.text
        return raw

    def get_out_trade_no(self):
        # 从某处获取订单号（一定是在库里有这么一个订单）
        return "8f8d6rhtiu6i3h"


print(MxPay.get_nonce_str())
# mpay = MxPay("!@")

# print(mpay.create_order("12", 89899, "192.179.22.1"))
# print(mpay.sign({"name": "yangzai", "age": 120}))
# print(mpay.create_image_code())

if __name__ == '__main__':
    mpay = MxPay()
    product_id = MxPay.get_nonce_str(12)
    out_trade_no = MxPay.get_nonce_str(12)
    return_data_dict, wxorder_return_code = mpay.create_order(total_fee=9988, spbill_create_ip="192.189.23.134",
                                                              out_trade_no=out_trade_no, body="腾讯充值中心-QQ会员充值",
                                                              product_id=product_id,
                                                              trade_type="NATIVE")
    print(wxorder_return_code)
