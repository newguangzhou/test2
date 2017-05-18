# -*- coding: utf-8 -*-
"""
使用dayu的短信发送服务
"""

import urllib
import logging

import traceback
import json
#from tornado import ioloop, gen
#from tornado.httpclient import AsyncHTTPClient
#import tornado.escape
from top import api
import top
#from taobao_sdk.top import api
#from taobao_sdk import top

def send_verify(code, product, phones):
    logging.debug("code:%s product:%s phones:%s", code, product, phones)
    req = api.AlibabaAliqinFcSmsNumSendRequest()
    req.set_app_info(top.appinfo("23566149",
                                 "f95d87510975317c9539d858c010f5a0"))
    req.extend = ""
    req.sms_type = "normal"
    req.sms_free_sign_name = "登录验证"
    req.sms_param = "{code:'%s',product:'%s'}" % (code, product)
    req.rec_num = phones
    req.sms_template_code = "SMS_18700741"
    try:
        resp = req.getResponse()
        print resp
        print resp["alibaba_aliqin_fc_sms_num_send_response"]["result"][
            "success"]
        return True
    except Exception, e:
        logging.exception(e)
        return False


def main():
    send_verify("123222", "小试试", 18666023586)


if __name__ == '__main__':
    main()