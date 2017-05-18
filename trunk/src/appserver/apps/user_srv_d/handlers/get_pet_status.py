# -*- coding: utf-8 -*-
import json
import urllib
import logging
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class GetPetStatusInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("GetPetStatusInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        conf = self.settings["appconfig"]

        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        token = None
        pet_id = -1

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            pet_id = int(self.get_argument("pet_id", -1))
        except Exception, e:
            logging.warning("GetPetStatusInfo, invalid args, %s",
                            self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:

            info = yield pet_dao.get_user_pets(uid, ("pet_id",
                                                     "pet_status", ))
            if not info:
                logging.warning("GetPetStatusInfo, not found, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            if pet_id != info["pet_id"]:
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            res["pet_status"] = info["pet_status"]
        except Exception, e:
            logging.error("GetPetStatusInfo, error, %s %s", self.dump_req(),
                          self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("GetPetStatusInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()