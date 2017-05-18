# -*- coding: utf-8 -*-
import json
import urllib
import logging
import traceback
from lib import error_codes
import datetime
from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class GetWifiList(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("OnGetDeviceSwitchLightStatus, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        device_dao = self.settings["device_dao"]
        conf = self.settings["appconfig"]

        res = {"status": error_codes.EC_SUCCESS}
        uid = None
        token = None
        device_imei = None

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            #device_imei = self.get_argument("imei", None)
        except Exception, e:
            logging.warning("GetWifiList, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        try:
            #st = yield self.check_token("OnGetPetInfo", res, uid, token)
            #if not st:
            #    return

            info = yield pet_dao.get_user_pets(uid,
                                               ("device_imei", "home_wifi"))
            if not info:
                logging.warning("GetWifiList, not found, %s", self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
            device_imei = info.get("device_imei", None)
            home_wifi = info.get("home_wifi", None)
            if device_imei is None or device_imei == "":
                res["status"] = error_codes.EC_DEVICE_NOT_EXIST
                self.res_and_fini(res)
                return
            res["data"] = []
            last_wifi = yield device_dao.get_last_wifi_info(device_imei)
            print "last_wifi", last_wifi
            if last_wifi is not None:
                create_date = last_wifi["create_date"]
                now = datetime.datetime.today()
                secs = (now - create_date).total_seconds()
                print "secs", secs
                if -30 < secs < 30:
                    tmp = utils.change_wifi_info(last_wifi["wifi_info"], True)
                    for item in tmp:
                        last_item = {}
                        last_item["wifi_ssid"] = item["wifi_ssid"]
                        last_item["wifi_bssid"] = item["wifi_bssid"]
                        last_item["wifi_power"] = item["deep"]
                        if home_wifi is not None and home_wifi[
                                "wifi_ssid"] == last_item[
                                    "wifi_ssid"] and home_wifi[
                                        "wifi_bssid"] == last_item[
                                            "wifi_bssid"]:
                            last_item["is_homewifi"] = 1
                        else:
                            last_item["is_homewifi"] = 0
                        res["data"].append(last_item)

        except Exception, e:
            logging.error("OnGetDeviceSwitchLightStatus, error, %s %s",
                          self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("OnGetPetInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()