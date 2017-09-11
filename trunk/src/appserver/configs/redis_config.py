# -*- coding: utf-8 -*-


class RedisConfig:
    def __init__(self, *args, **kwargs):
        debug_mode = 0
        if kwargs.has_key("debug_mode"):
            debug_mode = kwargs["debug_mode"]

        if debug_mode == 0:
            self.startup_nodes = [{"host": "127.0.0.1", "port": 6379}]
        else:
            self.startup_nodes = [{"host": "127.0.0.1", "port": 6379}]
