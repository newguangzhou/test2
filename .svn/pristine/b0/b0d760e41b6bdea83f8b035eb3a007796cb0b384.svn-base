# -*- coding: utf-8 -*-

import json
import urllib
import logging
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler


class PetFind(HelperHandler):
    @asynchronous
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnPetFind, %s", self.dump_req())
        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        terminal_rpc = self.settings["terminal_rpc"]
        uid = None
        token = None
        find_status = None
        pet_id = None
        res = {"status": error_codes.EC_SUCCESS}
        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            pet_id = int(self.get_argument("pet_id"))
            find_status = int(self.get_argument("find_status"))
        except Exception, e:
            logging.warning("OnPetFind, invalid args, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        if find_status not in (1, 2):
            logging.warning("OnPetFind, invalid args, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        # 检查token
        #st = yield self.check_token("OnOnPetWalk", res, uid, token)
        #if not st:
        #    return

        try:
            info = yield pet_dao.get_user_pets(uid, ("pet_id", "device_imei"))
            if info is None or pet_id != info["pet_id"]:
                logging.warning("OnPetFind, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return

            imei = info.get("device_imei", None)
            if imei is None:
                logging.warning("OnPetFind, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return
            gps_enable = 1 if find_status == 1 else 0
            get_res = yield terminal_rpc.send_command_params(
                imei=imei, gps_enable=gps_enable)

            if get_res["status"] == error_codes.EC_SEND_CMD_FAIL:
                res["status"] = error_codes.EC_SEND_CMD_FAIL
                self.res_and_fini(res)
                return

        except Exception, e:
            logging.warning("OnPetFind, sys_error, %s, exception %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        pet_status = 2 if find_status == 1 else 0

        try:
            yield pet_dao.update_pet_info(pet_id, pet_status=pet_status)
        except Exception, e:
            logging.warning("OnPetFind, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
