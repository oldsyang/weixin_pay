# -*- coding:utf-8 -8-

from io import BytesIO
from django.shortcuts import render, HttpResponse
from django.conf import settings
import qrcode
from wpay import MxPay
import json

out_trade_no_dict = set({})


def get_image(request):
    pro_id = request.GET.get("pro_id")
    if pro_id and request.session["code_info"]:
        code = request.session["code_info"].get(pro_id)
        stream = BytesIO()
        img_content = qrcode.make(code)
        img_content.save(stream, "png")
        return HttpResponse(stream.getvalue())
    else:
        return HttpResponse("啥也没有")


def search_order(request):
    '''
    
    Args:
        request: 

    Returns:
        {
            trade_state: "CLOSED",
            nonce_str: "befW1e1E4323J72XUS9g",
            return_code: "SUCCESS",
            return_msg: "OK",
            sign: "5D9211E283CB43w3F6552394712FFAF5D4F96",
            attach: null,
            mch_id: "1493987236453",
            out_trade_no: "7fZlA99331FrrA",
            trade_state_desc: "订单已关闭",
            appid: "w50923f6eqew240df3ae50",
            result_code: "SUCCESS"
            }

    '''
    # 查询订单号
    out_trade_no = request.GET.get("out_trade_no")
    transaction_id = request.GET.get("transaction_id")
    mpay = MxPay()

    # 这里不要多写out_trade_no和transaction_id只能填写一个，官方建议使用transaction_id（异步回调返回的）
    return_dict = mpay.search_order(**{"out_trade_no": out_trade_no, "transaction_id": transaction_id})
    # 记得要对返回数据做check验证，防止攻击
    return HttpResponse(json.dumps(return_dict))


def search_refund_order(request):
    '''

    Args:
        request: 

    Returns:
        {
            total_fee: "1",
            refund_channel_0: "ORIGINA23L",
            refund_id_0: "5000010488201712060232568553474",
            refund_status_0: "SUCCESS",
            refund_account_0: "REFUND_SOU3RCE_23UNSETTLED_FUNDS",
            nonce_str: "s49STy8K3UT23UKmEE",
            refund_fee_0: "1",
            return_msg: "OK",
            return_code: "SUCCESS",
            mch_id: "149392569292",
            out_trade_no: "w4UQJBhV23dW7z",
            refund_recv_accout_0: "支付用户的零钱",
            transaction_id: "42000000323820172312069515757841",
            refund_count: "1",
            appid: "wx652309f6e56240df323ae50",
            refund_success_time_0: "2017-12-06 20:02:49",
            out_refund_no_0: "ZIENxb23ALlV",
            cash_fee: "1",
            refund_fee: "1",
            result_code: "SUCCESS",
            sign: "16BCA22B352321DB54B5AC238C231A02DCE9D"
        }

    '''
    # 查询订单号
    out_trade_no = request.GET.get("out_trade_no")
    # 这里不要多写out_trade_no和transaction_id只能填写一个，官方建议使用transaction_id（异步回调返回的）
    mpay = MxPay()
    return_dict = mpay.search_refund_order(**{"out_trade_no": out_trade_no})
    # 记得要对返回数据做check验证，防止攻击
    return HttpResponse(json.dumps(return_dict))


def refund_order(request):
    '''
    退款操作：
        暂时只填必填字段，refund_desc 在官方是选填字段，但发现加入后会报错
    Args:
        request: 

    Returns:
        {
            cash_refund_fee: "1",
            coupon_refund_fee: "0",
            cash_fee: "1",
            refund_id: "5000010488201731423450602568553474",
            coupon_refund_count: "0",
            refund_channel: null,
            nonce_str: "9U0C90Wf3i834mpqazN",
            return_code: "SUCCESS",
            return_msg: "OK",
            sign: "7E3F0BC673118734628334C84137C50C4B7F",
            mch_id: "149392923492",
            out_trade_no: "w4UQ434JBhV3dW7z",
            transaction_id: "420045400304038201712069515757841",
            total_fee: "1",
            appid: "wx6509f6345e233440dfae50",
            out_refund_no: "ZIENx45334bALlV",
            refund_fee: "1",
            result_code: "SUCCESS"
        }
        
        {
            nonce_str: "uOgEI7piH3HSHYJUR",
            return_code: "SUCCESS",
            return_msg: "OK",
            sign: "B27B91E53B5183D2338844B9C6D23B685",
            mch_id: "14929323292",
            err_code_des: "订单已全额退款",
            appid: "wx09f236e240d233fae50",
            result_code: "FAIL",
            err_code: "ERROR"
        }
        
        {
            nonce_str: "EDsOhn10Ewe3kldtcuB",
            return_code: "SUCCESS",
            return_msg: "OK",
            sign: "718174E450AFBE583F1we744ED1D6F22196",
            mch_id: "14922339292",
            err_code_des: "商户订单号非法，请核实后再试",
            appid: "wx23609f623e2340dfae50",
            result_code: "FAIL",
            err_code: "ERROR"
        }

    '''
    # 查询订单号
    out_trade_no = request.GET.get("out_trade_no")
    transaction_id = request.GET.get("transaction_id")

    # 这里不要多写out_trade_no和transaction_id只能填写一个，官方建议使用transaction_id（异步回调返回的）
    mpay = MxPay()
    return_dict = mpay.refund(
        **{"transaction_id": transaction_id,
           "out_refund_no": MxPay.get_nonce_str(10), "total_fee": 1, "refund_fee": 1,
           "refund_desc": u"测试退款"})
    # 记得要对返回数据做check验证，防止攻击
    return HttpResponse(json.dumps(return_dict))


def close_order(request):
    '''
    
    Args:
        request: 

    Returns:
        {
            sub_mch_id: null,
            nonce_str: "s6pRrk5iNI3o3l4ezK",
            return_code: "SUCCESS",
            return_msg: "OK",
            sign: "C718936393CA4D0743C32EC1D178534C8B",
            mch_id: "149398376453",
            appid: "w50923f6e2403dfae50",
            result_code: "SUCCESS"
        }

    '''
    # 关闭订单号
    out_trade_no = request.GET.get("out_trade_no")

    # 这里不要多写out_trade_no和transaction_id只能填写一个，官方建议使用transaction_id（异步回调返回的）
    mpay = MxPay()
    return_dict = mpay.close_order(out_trade_no)
    # 记得要对返回数据做check验证，防止攻击
    return HttpResponse(json.dumps(return_dict))


def notify_url_event(request):
    '''
    用户支付后的异步通知（注意这里是https）
    Args:
           
    Returns:
        
        <xml><appid><![CDATA[wx6509f6e240dfae50]]></appid>
            <bank_type><![CDATA[CFT]]></bank_type>
            <cash_fee><![CDATA[1]]></cash_fee>
            <fee_type><![CDATA[CNY]]></fee_type>
            <is_subscribe><![CDATA[N]]></is_subscribe>
            <mch_id><![CDATA[14323929292]]></mch_id>
            <nonce_str><![CDATA[aCJv0SAwKY5Cxfi34mtCEM5SdNKexuXgnW]]></nonce_str>
            <openid><![CDATA[oHWl5w5M34hYM-ox2mn6Xatse7yCTs]]></openid>
            <out_trade_no><![CDATA[aHQDJyacUSGC]]></out_trade_no>
            <result_code><![CDATA[SUCCESS]]></result_code>
            <return_code><![CDATA[SUCCESS]]></return_code>
            <sign><![CDATA[C4F8B5B17A3E6203491A3B790A1D87ECEA]]></sign>
            <time_end><![CDATA[201712114144230]]></time_end>
            <total_fee>1</total_fee>
            <trade_type><![CDATA[NATIVE]]></trade_type>
            <transaction_id><![CDATA[4200000031201712112434025551875]]></transaction_id>
        </xml>

    '''
    print("有回调返回")
    params = MxPay.to_dict(request.body)
    if params.get("return_code") == "SUCCESS":
        # 说明通信正常

        if MxPay.check(params, settings.WX_MCH_KEY):  # 验证签名

            if params.get("result_code", None) == "SUCCESS":  # 业务正常
                # 商户订单号
                out_trade_no = params.get("out_trade_no")

                # 微信支付订单号（官方建议使用此号作为向微信查数据的凭证）
                transaction_id = params.get("out_trade_no")

                #  操作后台


                # 在处理好之后，一定要返回给微信
                xml_str = MxPay.get_xml({"return_code": "SUCCESS"})
                return HttpResponse(xml_str)



            else:
                print("{0}:{1}".format(params.get("err_code"), params.get("err_code_des")))
    else:
        # 类似于appid,mch_id等有错误
        print(params.get("return_msg").encode("utf-8"))


def home(request):
    '''
    下单入口
    Args:
        request: 

    Returns:

    '''

    # 先自己在系统中生成一份订单，拿到订单ID
    product_id = MxPay.get_nonce_str(12)
    out_trade_no = MxPay.get_nonce_str(12)
    print("out_trade_no:", out_trade_no)
    mpay = MxPay()
    return_data_dict, wxorder_return_code = mpay.create_order(total_fee=1, spbill_create_ip=request.META['REMOTE_ADDR'],
                                                              out_trade_no=out_trade_no, body="原子钟微信测试",
                                                              product_id=product_id,
                                                              trade_type="NATIVE")
    print("wxorder_return_code:", wxorder_return_code)
    request.session["code_info"] = {product_id: wxorder_return_code}
    return render(request, "index.html", {"pro_id": product_id})
