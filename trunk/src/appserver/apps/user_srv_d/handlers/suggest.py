# -*- coding=utf-8 -*-


from helper_handler import HelperHandler
class Suggest(HelperHandler):

    def post(self):
        return self._deal_request()

    def get(self):
        return self._deal_request()