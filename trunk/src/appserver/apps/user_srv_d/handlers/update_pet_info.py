# -*- coding: utf-8 -*-
import json
import urllib
import logging
import datetime
import traceback
from lib import error_codes

from tornado.web import asynchronous
from tornado import gen
from helper_handler import HelperHandler

from lib import utils
from lib import sys_config
from lib.sys_config import SysConfig


class UpdatePetInfo(HelperHandler):
    @gen.coroutine
    def _deal_request(self):
        logging.debug("UpdatePetInfo, %s", self.dump_req())

        self.set_header("Content-Type", "application/json; charset=utf-8")
        pet_dao = self.settings["pet_dao"]
        conf = self.settings["appconfig"]
        terminal_rpc = self.settings["terminal_rpc"]
        res = {"status": error_codes.EC_SUCCESS}

        uid = None
        pet_id = None
        nick = None
        logo_url = None
        logo_small_url = None
        birthday = None
        sex = None
        weight = None
        pet_type_id = None
        description = None
        imei = None

        try:
            uid = int(self.get_argument("uid"))
            token = self.get_argument("token")
            st = yield self.check_token("OnAddPetInfo", res, uid, token)
            if not st:
                return
            pet_id = int(self.get_argument("pet_id"))
            imei = self.get_argument("imei")
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
            pet_type_id = self.get_argument("pet_type_id", None)
            if pet_type_id is not None:
                pet_type_id = int(pet_type_id)
        except Exception, e:
            logging.warning("UpdatePetInfo, invalid args, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return

        if (sex is not None and sex not in
            (0, 1, 2)) or (weight is not None and
                           (weight > 1000 or weight < 0)) \
                or (pet_type_id is not None and pet_type_id not in (0, -1, 1, 2)):
            logging.warning("UpdatePetInfo, invalid args, %s", self.dump_req())
            res["status"] = error_codes.EC_INVALID_ARGS
            self.res_and_fini(res)
            return
        try:
            exist = yield pet_dao.is_pet_id_exist(pet_id, uid)
            if not exist:
                logging.warning("UpdatePetInfo, pet_id uid not exist, %s",
                                self.dump_req())
                res["status"] = error_codes.EC_PET_NOT_EXIST
                self.res_and_fini(res)
                return
        except Exception, e:
            logging.warning("UpdatePetInfo, is_pet_id_exist error, %s %s",
                            self.dump_req(), self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return
        info = {"mod_date": datetime.datetime.today()}
        if pet_type_id is not None:
            info["pet_type_id"] = pet_type_id
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

        # @017,25%1%0,3#2,5%15.3%1
        try:
            command = "017,25%%1%%0,3#2,5%%%f%%%d" % (float(info["weight"]), int(info["sex"]))
            print command
            get_res = yield terminal_rpc.send_j03(imei, command)
            res["status"] = get_res["status"]
        except Exception, e:
            logging.warning("add_pet_info to device, error, %s %s",
                            self.dump_req(), str(e))
            res["status"] = error_codes.EC_SEND_CMD_FAIL
            self.res_and_fini(res)
            return
        try:
            yield pet_dao.update_pet_info(pet_id, **info)
        except Exception, e:
            logging.warning("UpdatePetInfo, error, %s %s", self.dump_req(),
                            self.dump_exp(e))
            res["status"] = error_codes.EC_SYS_ERROR
            self.res_and_fini(res)
            return

# 成功
        logging.debug("UpdatePetInfo, success %s", self.dump_req())
        self.res_and_fini(res)

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()
