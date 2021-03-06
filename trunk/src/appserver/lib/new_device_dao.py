# -*- coding: utf-8 -*-

from tornado import gen

from new_device_mongo_dao import NewDeviceMongoDAO


class NewDeviceDAO:
    @staticmethod
    def new(*args, **kwargs):
        mongo_dao = NewDeviceMongoDAO(*args, **kwargs)
        inst = NewDeviceDAO(db_dao=mongo_dao)
        return inst

    def __init__(self, **kwargs):
        self._db_dao = kwargs["db_dao"]

    def __getattr__(self, attr):
        return getattr(self._db_dao, attr)
