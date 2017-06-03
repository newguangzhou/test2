# -*- coding: utf-8 -*-
import json


def new_device_off_line_msg():
    msg = {"type": "device",
           "signal": "offline", }
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")

def new_device_on_line_msg():
    msg = {"type": "device",
           "signal": "online", }
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")

def new_pet_not_home_msg():
    msg = {"type": "pet",
           "signal": "not-home", }
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")


def new_location_change_msg(latitude, longitude, location_time, radius):
    msg = {"type": "pet",
           "signal": "location-change",
           "data": {
               "latitude": latitude,
               "location_time": location_time,
               "longitude": longitude,
               "radius": radius
           }}
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")


def new_low_battery_msg(battery, if_ultra):
    signal = "ultra-low-battery" if if_ultra else "low-battery"
    msg = {"type": "device",
           "signal": signal,
           "data": {"battery_level": battery}}
    return json.dumps(msg, ensure_ascii=False, encoding="utf8")
