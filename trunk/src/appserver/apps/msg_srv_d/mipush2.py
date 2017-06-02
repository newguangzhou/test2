# -*- coding: utf-8 -*-
"""
使用官方的sdk
"""

from APISender import APISender
from base.APIMessage import *
from APITools import *
from APISubscribe import *
import logging


class MiPush2:
    def __init__(self, appsecret, app_pkg_name, debug_mode):
        self._appsecret = appsecret
        self._app_pkg_name = app_pkg_name
        self._debug_mode = debug_mode
        self._sender = APISender(self._appsecret)

    def send_to_alias_android(self,
                              str_uids,
                              title,
                              desc,
                              payload,
                              pass_through=0):
        message = PushMessage().restricted_package_name(
            self._app_pkg_name).payload(payload).pass_through(pass_through)
        if pass_through == 0:
            message = message.title(title).description(desc)
        recv = self._sender.send_to_alias(message.message_dict(), str_uids)
        logging.debug("on send_to_alias_android recv:%s", recv)