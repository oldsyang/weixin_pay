## 废话

[github源码](https://github.com/oldsyang/weixin_pay)

做了京东，支付宝和微信的python版本支付，发现只有微信支付开发文档是最用心去做的，讲解的非常仔细，还有大量的伪代码，说实话，实现起来真是没有难度，只是前期准备的东西有很多，比如要申请各种认证，至少到目前为止，我没有发现诸如京东支付或者支付宝支付那样的测试环境供普通开发者去调试

## 技术描点

微信支付方式非常多，详见：https://pay.weixin.qq.com/wiki/doc/api/index.html。

我在这里是用的扫码支付，用于pc网站。首先要准备的是两个重要的帐号：公众帐号ID和商户号。所以要先去以公司的名义申请商户资质

各种申请好了之后，找到【公众帐号ID】和【商户号】就可行，【公众帐号ID】藏的比较隐秘，不太好找，要用心找。

扫描支付有两种模式：模式一和模式二：https://pay.weixin.qq.com/wiki/doc/api/native.php?chapter=6_5

我推荐使用模式二，应该说也是官方推荐的，因为它简化了很多步骤，让流程更容易让开发者理解

业务流程说明：

```
（1）商户后台系统根据用户选购的商品生成订单。
（2）用户确认支付后调用微信支付【统一下单API】生成预支付交易；
（3）微信支付系统收到请求后生成预支付交易单，并返回交易会话的二维码链接code_url。
（4）商户后台系统根据返回的code_url生成二维码。
（5）用户打开微信“扫一扫”扫描二维码，微信客户端将扫码内容发送到微信支付系统。
（6）微信支付系统收到客户端请求，验证链接有效性后发起用户支付，要求用户授权。
（7）用户在微信客户端输入密码，确认支付后，微信客户端提交授权。
（8）微信支付系统根据用户授权完成支付交易。
（9）微信支付系统完成支付交易后给微信客户端返回交易结果，并将交易结果通过短信、微信消息提示用户。微信客户端展示支付交易结果页面。
（10）微信支付系统通过发送异步消息通知商户后台系统支付结果。商户后台系统需回复接收情况，通知微信后台系统不再发送该单的支付通知。
（11）未收到支付通知的情况，商户后台系统调用【查询订单API】。
（12）商户确认订单已支付后给用户发货。
```

看了上面的流程简介，是不是感觉非常简单

一. 统一下单API

接口：https://api.mch.weixin.qq.com/pay/unifiedorder

接口参数说明：https://pay.weixin.qq.com/wiki/doc/api/native.php?chapter=9_1



二. 签名

微信的签名是三种支付方式中最简单的，没有使用公私钥的非对称加解密验签，而是用的MD5（注意在商户平台里设置MD5）。

详情请见：https://pay.weixin.qq.com/wiki/doc/api/native.php?chapter=4_3

看看人家的签名步骤，就差在你背后教你手写代码了。还是公司大啊

签名完的xml格式：

```xml
<xml>
   <appid>wx2421b1c4370ec43b</appid>
   <attach>支付测试</attach>
   <body>JSAPI支付测试</body>
   <mch_id>10000100</mch_id>
   <detail><![CDATA[{ "goods_detail":[ { "goods_id":"iphone6s_16G", "wxpay_goods_id":"1001", "goods_name":"iPhone6s 16G", "quantity":1, "price":528800, "goods_category":"123456", "body":"苹果手机" }, { "goods_id":"iphone6s_32G", "wxpay_goods_id":"1002", "goods_name":"iPhone6s 32G", "quantity":1, "price":608800, "goods_category":"123789", "body":"苹果手机" } ] }]]></detail>
   <nonce_str>1add1a30ac87aa2db72f57a2375d8fec</nonce_str>
   <notify_url>http://wxpay.wxutil.com/pub_v2/pay/notify.v2.php</notify_url>
   <openid>oUpF8uMuAJO_M2pxb1Q9zNjWeS6o</openid>
   <out_trade_no>1415659990</out_trade_no>
   <spbill_create_ip>14.23.150.211</spbill_create_ip>
   <total_fee>1</total_fee>
   <trade_type>JSAPI</trade_type>
   <sign>0CB01533B8C1EF103065174F50BCA001</sign>
</xml>
```

然后用requests库发送一个post请求就ok了

三. 生成二维码

在下单成功之后，会返回二维码的内容，拿到这个之后，自己在后台生成一个二维码图片给用户就可以了，是不是非常简单。

四. 异步回调

在用户扫码并支付成功之后，老规矩会触发一个异步通知，这个通知会通知支付的状态，一定要以这个通知为标准。处理完逻辑之后，一定要记得返回一个确认信息给微信

```
# 在处理好之后，一定要返回给微信
xml_str = MxPay.get_xml({"return_code": "SUCCESS"})
return HttpResponse(xml_str)
```

而且一定要记住，当用户支付成功之后，会不停的往你设定的这个异步回调地址发post请求，直到你回复了，才停止发送。所以在处理的时候，一定要判断是否处理过了

五. 申请退款

涉及到退款，那可马虎不得，微信也说了，下单随便下，退款那得慢慢来。所以在这里退款的操作，要特别注意的是需要带证书（微信支付签发的）

```
requests.post(url, data=json.dumps(xml_str, ensure_ascii=False),cert=(self.API_CLIENT_CERT_PATH, self.API_CLIENT_KEY_PATH))
```


整体来说，微信支付很简单，看看文档肯定是没有问题的。

setting文件的一些配置

```python
# 微信分配的公众账号ID
APP_ID = "wx6534240dfae560"
# 微信支付分配的商户号
MCH_ID = "13459829292"
# 私钥（在商户后台设置的就是这个值，注意修改任何一段需要同步修改）
WX_MCH_KEY = "D3EG723wIxgv2jnEgkr38yNJ8cP05D6aoT"

# 异步接收微信支付结果通知的回调地址，通知url必须为外网可访问的url，不能携带参数。
ASYN_NOTIFY_URL = "http://xxxxxx.com:8888/test/weixin/"

# 统一下单地址
ORDER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"

# 查询订单url
SEARCH_URL = "https://api.mch.weixin.qq.com/pay/orderquery"
# 关闭订单url
CLOSE_URL = "https://api.mch.weixin.qq.com/pay/closeorder"

# 申请退款url
REFUND_URL = "https://api.mch.weixin.qq.com/secapi/pay/refund"

# 查询申请退款
SEARCH_REFUND_URL = "https://api.mch.weixin.qq.com/pay/refundquery"

# 服务器存放证书路径（微信支付签发的）
API_CLIENT_CERT_PATH = "/path/your/cert/apiclient_cert.pem"
API_CLIENT_KEY_PATH = "/path/your/cert/apiclient_key.pem"
```