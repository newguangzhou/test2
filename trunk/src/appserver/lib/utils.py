# -*- coding: utf-8 -*-

import datetime
import time
import logging
import copy
import re
from tornado.concurrent import Future
from tornado import gen
import math
from sys_config import DOG_CONFIG, DOG_NAME_CONFIG


def date2str(dt, no_time=False):
    if isinstance(dt, datetime.datetime):
        if no_time:
            return "%02u-%02u-%02u" % (dt.year, dt.month, dt.day)
        else:
            return "%02u-%02u-%02u %02u:%02u:%02u" % (
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    elif isinstance(dt, datetime.date):
        return "%02u-%02u-%02u" % (dt.year, dt.month, dt.day)
    else:
        return ""


def str2date(str, format="%Y%m%d"):
    st = time.strptime(str, format)
    return datetime.date.fromtimestamp(time.mktime(st))


def str2datetime(str, format="%Y%m%d%H%M%S"):
    st = time.strptime(str, format)
    return datetime.datetime.fromtimestamp(time.mktime(st))


def date2int(dt):
    return int(time.mktime(dt.timetuple()))


def gen_select_sql(table, fnames, cond, iswhere=True, limit=None):
    sql = "select "
    for i in range(0, len(fnames)):
        sql += fnames[i]
        if i != len(fnames) - 1:
            sql += ","
    sql += " from %s " % (table, )
    if cond is not None:
        if iswhere:
            sql += "where "
        sql += cond
    if limit is not None:
        sql += "limit %u" % limit
    return sql


def gen_update_sql(table, cond, fnames):
    sql = "update %s set " % (table)
    for i in range(0, len(fnames)):
        sql += fnames[i] + "=%s"
        if i != len(fnames) - 1:
            sql += ","
    if cond is not None:
        sql += " where %s" % (cond, )
    return sql


def gen_insert_sql(table, fnames):
    sql1 = "insert into %s(" % (table, )
    sql2 = " values("
    for i in range(0, len(fnames)):
        sql1 += fnames[i]
        sql2 += "%s"
        if i != len(fnames) - 1:
            sql1 += ","
            sql2 += ","
    sql1 += ")"
    sql2 += ")"

    return sql1 + sql2


def recover_log(title, **kwargs):
    msg = "[recover] title=\"%s\"," % (title, )
    i = 0
    for (k, v) in kwargs.items():
        if isinstance(v, int) or isinstance(v, float):
            msg += "%s=%s" % (k, str(v))
        elif isinstance(v, str):
            msg += "%s=\"%s\"" % (k, v)
        else:
            msg += "%s=\"%s\"" % (k, str(v))
        if i != len(kwargs) - 1:
            msg += ","
        i += 1
    logging.error(msg)


def new_mongo_row(row_define):
    tmp = copy.deepcopy(row_define)
    ret = {}
    for (k, v) in tmp.items():
        ret[k] = v[0]
    return ret


def validate_mongo_row(row, row_define):
    print row, row_define
    for (k, v) in row.items():
        if v is None:
            return (False, k)

        if not row_define.has_key(k):
            print 1, k, v
            return (False, k)

        if not isinstance(v, row_define[k][1]):
            print 2, k, v, row_define[k][1], type(v)
            return (False, k)
    return (True, None)


def validate_mongo_row_cols(row_define, **cols):
    for (k, v) in cols.items():
        if not row_define.has_key(k):
            return (False, k)
        if not isinstance(v, row_define[k][1]):
            return (False, k)
    return (True, None)


def has_mongo_row_col(row_define, colname):
    return row_define.has_key(colname)


def is_mobile_num(val):
    if len(val) != 11:
        return False

    for c in val:
        try:
            int(c)
        except:
            return False

    if val[0] == '0':
        return False

    return True


def merge(times):
    saved = list(times[0])
    ret = []
    for st, en in sorted([sorted(t) for t in times]):
        if st <= saved[1]:
            saved[1] = max(saved[1], en)
        else:
            ret.append(tuple(saved))
            saved[0] = st
            saved[1] = en
    ret.append(tuple(saved))
    return ret


def is_valid_phone_num(phone_num):
    p = re.compile(
        '^((13[0-9])|(14[0-9])|(15[0-9])|(16[0-9])|(17[0-9])|(18[0-9]))\d{8}$')
    return p.match(phone_num)


def calculate_dog_sport(month, weight, id, default_id=0):
    sport = 0
    dog_info = DOG_CONFIG.get(id, None)
    if dog_info is None:
        dog_info = DOG_CONFIG.get(default_id, None)
    if dog_info is not None:
        sport = _calculate_dog_sport(month, weight, dog_info)
    return sport


def calculate_dog_sport_by_name(month, weight, name, default_name):
    sport = 0
    dog_info = DOG_NAME_CONFIG.get(name, "")
    if dog_info is None:
        dog_info = DOG_NAME_CONFIG.get(default_name, "")
    if dog_info is not None:
        sport = _calculate_dog_sport(month, weight, dog_info)
    return sport


def _calculate_dog_sport(month, weight, dog_info):
    ere = math.pow(math.pow(70 * weight, 3), 1.0 / 4)
    if 0 <= month <= 4:
        sport = dog_info["rer_config"][0] * ere
    elif 4 < month <= 96:
        sport = dog_info["rer_config"][1] * ere
    else:
        sport = dog_info["rer_config"][2] * ere
    return sport


def change_wifi_info(mac, need_deep=False):
    ret = []
    tmp = mac.split("|")
    for item in tmp:
        if item != "":
            tmp2 = item.split(",")
            print "tmp2:", tmp2
            if len(tmp2) != "":
                info = {"wifi_ssid": tmp2[2], "wifi_bssid": tmp2[0]}
                if need_deep:
                    info["deep"] = tmp2[1]
                ret.append(info)
            #for item2 in tmp2:

    return ret