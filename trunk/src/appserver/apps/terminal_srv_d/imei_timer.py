# -*- coding: utf-8 -*-
from lib import sorted_set
import time
import logging
from tornado.ioloop import IOLoop

logger = logging.getLogger(__name__)


class ImeiTimer:
    def __init__(self, imei_timeout=8 * 60, check_timeout=10, check_num=5):
        self.imei_dict = sorted_set.SortedSet()
        self.imei_timeout = imei_timeout
        self.check_timeout = check_timeout
        self.check_num = check_num
        self.on_imeis_expire = None

    def set_on_imeis_expire(self, on_imeis_expire_func):
        self.on_imeis_expire = on_imeis_expire_func

    def add_imei(self, imei):
        now = int(time.time())
        self.imei_dict.zadd(imei, now)
        logger.debug("add imei:%s now:%d", imei, now)

    def start(self):
        IOLoop.instance().call_later(self.check_timeout, self.check)

    def check(self):
        print "timer check"

        expire_imeis = self.get_expire_imeis(self.check_num)

        if len(expire_imeis) != 0 and self.on_imeis_expire != None:
            self.on_imeis_expire(expire_imeis)

        IOLoop.instance().call_later(self.check_timeout, self.check)

    def get_expire_imeis(self, num):
        imei_with_scores = self.imei_dict.zrevrangebyscore(0, num)
        now = int(time.time())
        expire_imeis = []
        for key, score in imei_with_scores:
            if score - now < self.imei_timeout:
                expire_imeis.append(key)
                self.imei_dict.zrem(key)
                logger.debug("zrem imei:%s time:%d now:%d", key, score, now)
            else:
                break
        return expire_imeis
