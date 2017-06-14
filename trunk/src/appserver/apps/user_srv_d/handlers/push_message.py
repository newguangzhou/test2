# -*- coding: utf-8 -*-

import tornado.web
import json
import urllib

import logging
import traceback

from tornado.web import asynchronous
from tornado import gen
from tornado.httpclient import AsyncHTTPClient

from lib import error_codes
from lib import sys_config
from lib.sys_config import SysConfig
from lib import utils
from lib import push_msg
from helper_handler import HelperHandler


class PushMessageCmd(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPushMessage, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")

        conf = self.settings["appconfig"]
        msg_rpc = self.settings["msg_rpc"]

        res = {"status": error_codes.EC_SUCCESS}

        # 获取请求参数
        uid = None
        try:
            uid = self.get_argument("uid")
        except Exception, e:
            logging.warning("OnPushMessage, invalid args, %s %s",
                            self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        msg = push_msg.new_remot_login_msg()

        try:
            yield msg_rpc.push_ios(uids=str(uid),
                                            payload=msg)
        except Exception, e:
            logging.warning("OnPushMessage, invalid args, %s %s",
                            self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        # 成功
        logging.debug("OnPushmessage, success %s",
                      self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
