# -*- coding: utf-8 -*-
import json
import urllib
import logging
import datetime
import traceback
from lib import error_codes
import pymongo
from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class AddPetInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("AddPetInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        device_dao = self.settings["device_dao"]
        terminal_rpc = self.settings["terminal_rpc"]
        conf = self.settings["appconfig"]
        gid_rpc = self.settings["gid_rpc"]
        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        nick = None
        logo_url = None
        logo_small_url = None
        birthday = None
        sex = None
        weight = None
        pet_type_id = 1
        description = None
        reboot = None

        try:
            uid = int(self.get_argument("uid"))
            pet_type_id = int(self.get_argument("pet_type_id"))
            token = self.get_argument("token")
            reboot = self.get_argument("reboot", 1)
            st = yield self.check_token("OnAddPetInfo", res, uid, token)
            if not st:
                return

            nick = self.get_argument("nick", None)
            logo_url = self.get_argument("logo_url", None)
            logo_small_url = self.get_argument("logo_small_url", None)
            sex = self.get_argument("sex", None)
            if sex is not None:
                sex = int(sex)
            birthday = self.get_argument("birthday", None)
            if birthday is not None:
                birthday = utils.str2date(birthday, "%Y-%m-%d")
                birthday = datetime.datetime(birthday.year, birthday.month,
                                             birthday.day)
            weight = self.get_argument("weight", None)
            if weight is not None:
                weight = float(weight)
            description = self.get_argument("description", None)
        except Exception, e:
            logging.warning("AddPetInfo, invalid args, %s %s", self.dump_req(),
                            str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        if (sex is not None and sex not in (1, 2)) or (
                weight is not None and (weight > 1000 or weight < 0)
                or (pet_type_id is not None and pet_type_id not in (-1, 1, 2))):
            logging.warning("AddPetInfo, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)

        pet_id = yield gid_rpc.alloc_pet_gid()
        device_info = yield device_dao.get_device_info_by_uid(uid,("imei",))
        imei = device_info["imei"]
        info = {"pet_type_id": pet_type_id, "uid": uid}
        info["device_imei"] = imei
        info["uid"] = uid
        if nick is not None:
            info["nick"] = nick
        if logo_url is not None:
            info["logo_url"] = logo_url
        if sex is not None:
            info["sex"] = sex
        if birthday is not None:
            info["birthday"] = birthday
        if logo_small_url is not None:
            info["logo_small_url"] = logo_small_url
        if description is not None:
            info["description"] = description
        if weight is not None:
            info["weight"] = weight
        try:
            yield pet_dao.update_pet_info(pet_id, **info)
        except pymongo.errors.DuplicateKeyError, e:
            res["status"] = error_codes.EC_EXIST
            self.res_and_fini(res)
            return
        except Exception, e:
            logging.warning("AddPetInfo, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        res["pet_id"] = pet_id

        # @017,25%1%0,3#2,5%15.3%1
        try:
            command = "017,25%%1%%0,3#2,5%%%f%%%d" % (info["weight"], info["sex"])
            print command
            get_res = yield terminal_rpc.send_j03(imei,command)
            res["status"] = get_res["status"]
        except Exception, e:
            logging.warning("add_pet_info to device, error, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

        # if reboot:
        #     try:
        #         terminal_rpc.send_j03(imei, "020")
        #     except Exception, e:
        #         logging.warning("reboot device in add_pet_info, error, %s %s",
        #                 self.dump_req(), str(e))
        #         res["status"] = error_codes.EC_SYS_ERROR
        #         self.res_and_fini(res)
        # else:
        # try:
        #     yield terminal_rpc.send_j13(imei)
        # except Exception, e:
        #     logging.warning("get wifi list in add_pet_info, error, %s %s",
        #             self.dump_req(), str(e))

        # 成功
        logging.debug("AddPetInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
