# -*- coding: utf-8 -*-

import traceback
import struct
import StringIO
import time
import datetime
import pdb
from test_data import TEST_S2C_COMMAND_DATA
import logging
from tornado import gen
from terminal_base import terminal_proto, terminal_commands, terminal_packets, util
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from get_location import get_location_by_wifi, get_location_by_bts_info, get_location_by_mixed, convert_coordinate
_TERMINAL_CONN_MAX_BUFFER_SIZE = 2 * 1024 * 1024  # 2M
logger = logging.getLogger(__name__)

from lib import utils
from lib import push_msg

LOW_BATTERY = 25
ULTRA_LOW_BATTERY = 15


class TerminalHandler:
    executor = ThreadPoolExecutor(5)

    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            self.conn_mgr = args[0]
        else:
            self.conn_mgr = kwargs["conn_mgr"]

        self.debug = False
        if len(args) > 1:
            self.debug = args[1]
        elif kwargs.has_key("debug"):
            self.debug = kwargs["debug"]

        self.imei_timer_mgr = kwargs.get("imei_timer_mgr", None)
        if self.imei_timer_mgr is None:
            if len(args) > 2:
                self.imei_timer_mgr = args[2]

        self._broadcastor = kwargs.get("broadcastor", None)
        if self._broadcastor is None:
            if len(args) > 3:
                self._broadcastor = args[3]

        self.op_log_dao = kwargs.get("op_log_dao", None)
        self.new_device_dao = kwargs.get("new_device_dao", None)
        self.pet_dao = kwargs.get("pet_dao", None)
        self.msg_rpc = kwargs.get("msg_rpc", None)

        #self.terminal_proto_ios = {}

        self.terminal_proto_guarder = {}

    def OnOpen(self, conn_id):
        conn = self.conn_mgr.GetConn(conn_id)
        logger.info("Terminal conn is opened, id=%u peer=%s", conn_id,
                    conn.GetPeer())
        proto_io = terminal_proto.ProtoIO()
        self.terminal_proto_guarder[conn_id] = terminal_proto.ProtoIoGuarder(
            proto_io)
        return True

    @gen.coroutine
    def OnData(self, conn_id, data):
        conn = self.conn_mgr.GetConn(conn_id)

        logger.debug("onData conn_id:%d data:%s hex_data:%s ", conn_id, data,
                     data.encode('hex'))
        guarder = self.terminal_proto_guarder.get(conn_id, None)
        if guarder is None:
            return
        proto_io = yield guarder.get()

        # Check buffer
        if proto_io.read_buff.GetSize() + len(
                data) >= _TERMINAL_CONN_MAX_BUFFER_SIZE:
            logger.error(
                "Terminal conn read buffer is overflow, id=%u peer=%s",
                conn_id, conn.GetPeer())
            conn.close()
            return
            # Write to buffer
        proto_io.read_buff.AppendData2(data)
        #logger.debug("dump1:%s", proto_io.read_buff.Dump())
        # Read packets
        try:
            while True:
                header, body = proto_io.Read()
                if header is None:
                    break
                if header == terminal_proto.SIMPLE_HEART:
                    imei = self._broadcastor.get_imei_by_conn(conn_id)
                    logger.info(
                        "Receive a terminal packet simple heart id=%u peer=%s imei=%s",
                        conn_id, conn.GetPeer(), imei)
                    if imei is not None:
                        self._OnOpLog("[]", imei)
                        self.imei_timer_mgr.add_imei(imei)
                    continue
                logger.info(
                    "Receive a terminal packet, header=\"%s\" body=\"%s\" id=%u peer=%s",
                    str(header), body, conn_id, conn.GetPeer())

                # Dispatch
                disp_status = True
                if header.directive == "J01":  # 上传位置
                    disp_status = yield self._OnReportLocationInfoReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J02":  # 上传健康信息
                    disp_status = yield self._OnReportHealthInfoReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "R03":  # 发送远程命令设备回应的ack
                    disp_status = yield self._OnSendCommandAck(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J12":  # 设备发送的心跳请求
                    disp_status = yield self._OnHeartbeatReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J17":  # 设备上传状态数据
                    disp_status = yield self._OnReportTerminalStatusReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J18":  # 设备上传日志数据
                    disp_status = yield self._OnUploadTerminalLogReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J04":
                    disp_status = yield self._OnSyncCommandReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J16":
                    disp_status = yield self._OnUploadStationLocationReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "J15":
                    disp_status = yield self._OnGpsSwitchReq(
                        conn_id, header, body, conn.GetPeer())
                elif header.directive == "R13":
                    disp_status = yield self._OnReportLocationInfoReq(
                        conn_id, header, body, conn.GetPeer(), False)
                else:
                    logger.warning(
                        "Unknown directive, directive=\"%s\" id=%u peer=%s",
                        header.directive, conn_id, conn.GetPeer())

                if not disp_status:
                    conn.close()
                    return
        except Exception, e:
            logger.exception("id=%u peer=%s,Exception:%s", conn_id, conn.GetPeer(), e)
            conn.close()
            return

        guarder.release()
        return

    def OnError(self, conn_id, errno):
        logger.warning("Terminal conn has an error, id=%u errno=%u peer=%s",
                       conn_id, errno,
                       self.conn_mgr.GetConn(conn_id).GetPeer())

    def OnClose(self, conn_id, is_eof):
        conn = self.conn_mgr.GetConn(conn_id)
        if is_eof:
            logger.warning("Terminal conn is closed by peer, peer=\"%s\"",
                           conn.GetPeer())
        else:
            logger.warning("Terminal conn is closed, info=\"%s\"",
                           conn.GetPeer())

        if self.terminal_proto_guarder.has_key(conn_id):
            del self.terminal_proto_guarder[conn_id]

        self._broadcastor.un_register_conn(conn_id)

    def OnTimeout(self, conn_id):
        pass

    def _OnOpLog(self, content, imei):
        self.op_log_dao.add_op_info(imei=unicode(imei),
                                    content=unicode(content))

    @gen.coroutine
    def _send_res(self, conn_id, ack, imei, peer):
        str_ack = str(ack)
        ret = yield self.conn_mgr.Send(conn_id, str_ack)
        self._OnOpLog("s2c send_data:%s peer:%s ret:%s" %
                      (ack.orgin_data(), peer, str(ret)), imei)
        raise gen.Return(ret)

    @gen.coroutine
    def _OnReportLocationInfoReq(self,
                                 conn_id,
                                 header,
                                 body,
                                 peer,
                                 need_send_ack=True):
        # Parse packet
        pk = terminal_packets.ReportLocationInfoReq()
        pk.Parse(body)
        str_pk = str(pk)

        logger.debug(
            "OnReportLocationInfoReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        self._OnOpLog('c2s header=%s pk=%s peer=%s' % (header, str_pk, peer),
                      pk.imei)

        if need_send_ack:
            ack = terminal_packets.ReportLocationInfoAck(header.sn)
            yield self._send_res(conn_id, ack, pk.imei, peer)

        locator_time = pk.location_info.locator_time
        lnglat = []
        lnglat2 = []
        lnglat3 = []
        radius = -1
        radius2 = -1
        radius3 = -1

        if pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_GPS:

            ret = convert_coordinate((float(pk.location_info.longitude),
                                      float(pk.location_info.latitude)), "gps")
            if ret is not None:
                lnglat = [ret[0], ret[1]]

        elif pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_STATION:
            bts_info, near_bts_infos = util.split_locator_station_info(
                pk.location_info.station_locator_data)
            ret = yield self.get_location_by_bts_info(pk.imei, bts_info,
                                                      near_bts_infos)
            if ret is not None:
                lnglat = [ret[0], ret[1]]
                radius = ret[2]
        elif pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_MIXED:
            bts_info, near_bts_infos = util.split_locator_station_info(
                pk.location_info.station_locator_data)

            ret = yield self.get_location_by_mixed(
                pk.imei, bts_info, near_bts_infos, pk.location_info.mac)

            if ret is not None:
                lnglat = [ret[0], ret[1]]
                radius = ret[2]

            ret2 = yield self.get_location_by_wifi(pk.imei,
                                                   pk.location_info.mac)
            if ret2 is not None:
                lnglat2 = [ret2[0], ret2[1]]
                radius2 = ret2[2]

            ret3 = yield self.get_location_by_bts_info(pk.imei, bts_info,
                                                       near_bts_infos)
            if ret3 is not None:
                lnglat3 = [ret3[0], ret3[1]]
                radius3 = ret3[2]

        else:
            logger.warning("imei:%s location fail", pk.imei)
        pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid", "home_wifi", "common_wifi", "target_energy"),
                                                   device_imei=pk.imei)
        if pet_info is None:
            logger.error("imei:%s pk:%s not found pet_info", pk, str_pk)
        if len(lnglat) != 0:
            location_info = {"lnglat": lnglat,
                             "radius": radius,
                             "locator_time": locator_time}
            if len(lnglat2) != 0:
                location_info["lnglat2"] = lnglat2
                location_info["radius2"] = radius2
            if len(lnglat3) != 0:
                location_info["lnglat3"] = lnglat3
                location_info["radius3"] = radius3
            logger.info("imei:%s pk:%s location:%s", pk, str_pk,
                        str(location_info))
            if pet_info is not None:
                yield self.pet_dao.add_location_info(pet_info["pet_id"],
                                                     pk.imei, location_info)
                uid = pet_info.get("uid", None)
                if uid is not None:
                    msg = push_msg.new_location_change_msg(
                        "%.7f" % lnglat[1], "%.7f" % lnglat[0],
                        int(time.mktime(locator_time.timetuple())), radius)
                    try:
                        yield self.msg_rpc.push_android(uids=str(uid),
                                                        payload=msg,
                                                        pass_through=1)
                        yield self.msg_rpc.push_ios(uids=str(uid),
                                                        payload=msg)
                    except Exception, e:
                        logger.exception(e)
        now_time = datetime.datetime.now()
        yield self.new_device_dao.update_device_info(
            pk.imei,
            status=pk.status,
            electric_quantity=pk.electric_quantity,
            j01_repoter_date = now_time)

        battery_status = 0
        if pk.electric_quantity < LOW_BATTERY:
            battery_status = 1
            if pk.electric_quantity < ULTRA_LOW_BATTERY:
                battery_status = 2
        yield self._SendBatteryMsg(pk.imei, pk.electric_quantity, battery_status, now_time)

        if pet_info is not None:
            sport_info = {}
            sport_info["diary"] = datetime.datetime.combine(
                datetime.date.today(), datetime.time.min)
            sport_info["step_count"] = pk.step_count
            sport_info["distance"] = pk.distance
            sport_info["calorie"] = pk.calorie
            sport_info["target_energy"] = pet_info.get("target_energy",0)
            yield self.pet_dao.add_sport_info(pet_info["pet_id"], pk.imei,
                                              sport_info)

            if pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_MIXED:
                wifi_info = utils.change_wifi_info(pk.location_info.mac)
                common_wifi = pet_info.get("common_wifi", None)
                home_wifi = pet_info.get("home_wifi", None)
                new_common_wifi = utils.get_new_common_wifi(common_wifi,wifi_info,home_wifi)
                uid = pet_info.get("uid", None)
                if uid is not None:
                    is_in_home = utils.is_in_home(home_wifi, new_common_wifi, wifi_info)
                    self._SendPetInOrNotHomeMsg(pk.imei, is_in_home)
                yield self.pet_dao.add_common_wifi_info(pet_info["pet_id"],
                                                        new_common_wifi)

        if pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_MIXED:
            yield self.new_device_dao.report_wifi_info(pk.imei,
                                                       pk.location_info.mac)

        raise gen.Return(True)

    @gen.coroutine
    def _OnReportHealthInfoReq(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.ReportHealthInfoReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        logger.debug(
            "OnReportHealthInfoReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)
        # Ack
        sleep_data = []
        pet_info = yield self.pet_dao.get_pet_info(("pet_id", ),
                                                   device_imei=pk.imei)
        if pet_info is None:
            logger.error("imei:%s pk:%s not found pet_info", pk, str_pk)
        else:
            try:
                for item in pk.sleep_data:
                    tmp = terminal_proto.FieldDict(item.fields)
                    sleep_data.append(tmp)
                ret = yield self.pet_dao.add_sleep_info(pet_info["pet_id"],
                                                        pk.imei, sleep_data)

            except Exception, e:
                logger.exception(e)
        ack = terminal_packets.ReportHealthInfoAck(header.sn)
        yield self._send_res(conn_id, ack, pk.imei, peer)
        raise gen.Return(True)

    @gen.coroutine
    def _OnSendCommandAck(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.SendCommandAck()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "OnSendCommandAck, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnHeartbeatReq(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.HeatbeatReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s parse_data=%s peer=%s' %
                      (header, body, str_pk, peer), pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.info(
            "OnHeartbeatReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        # Ack
        ack = terminal_packets.HeatbeatAck(header.sn)
        yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _SendBatteryMsg(self, imei, battery, battery_statue, datetime):
        pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid"),
                                                   device_imei=imei)
        if pet_info is not None:
            uid = pet_info.get("uid", None)
            if uid is None:
                logger.warning("imei:%s uid not find", imei)
                return
            msg = push_msg.new_now_battery_msg(utils.date2str(datetime), battery, battery_statue)
            try:
                yield self.msg_rpc.push_android(uids=str(uid),
                                                payload=msg,
                                                pass_through=1)
                yield self.msg_rpc.push_ios_useraccount(uids=str(uid),
                                            payload=msg)
            except Exception, e:
                logger.exception(e)
        else:
            logger.warning("imei:%s uid not find", imei)

    @gen.coroutine
    def _OnReportTerminalStatusReq(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.ReportTerminalStatusReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "OnReportTerminalStatusReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        yield self.new_device_dao.update_device_info(
            pk.imei,
            iccid=unicode(pk.iccid),
            hardware_version=unicode(pk.hardware_version),
            software_version=unicode(pk.software_version),
            electric_quantity=pk.electric_quantity)

        now_time = datetime.datetime.now()
        battery_status = 0
        if pk.electric_quantity < LOW_BATTERY:
            battery_status = 1
            if pk.electric_quantity < ULTRA_LOW_BATTERY:
                battery_status = 2
        yield self._SendBatteryMsg(pk.imei, pk.electric_quantity, battery_status, now_time)

        yield self._SendOnlineMsg(pk.imei, pk.electric_quantity, now_time)

        # Ack
        ack = terminal_packets.ReportTerminalStatusAck(header.sn, 0)
        yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnSyncCommandReq(self, conn_id, header, body, peer):
        pk = terminal_packets.SyncCommandReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "OnSyncCommandReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        # Ack
        #command_pk = terminal_commands.SOS(("18666023586", "18666023585"))
        command_pk = TEST_S2C_COMMAND_DATA.get(pk.command, None)
        if command_pk is None:
            logger.error("OnSyncCommandReq command:%s not find", pk.command)
        else:
            ack = terminal_packets.SyncCommandResp(header.sn, command_pk, 0)
            yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnUploadTerminalLogReq(self, conn_id, header, body, peer):
        # Parse packet
        pk = terminal_packets.UploadTerminalLogReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "OnUploadTerminalLogReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        log_items = []
        try:
            log_items = [terminal_proto.FieldDict(item.fields)
                         for item in pk.log_items]
        except Exception, e:
            pass
        yield self.new_device_dao.add_terminal_log(pk.imei, log_items)
        # Ack
        ack = terminal_packets.UploadTerminalLogAck(header.sn, 0)
        yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnUploadStationLocationReq(self, conn_id, header, body, peer):
        pk = terminal_packets.UploadStationReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "_OnUploadStationLocationReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)
        ret = yield self.get_location_by_bts_info(
            pk.imei, pk.station_locator_data, None)
        lng = float(0)
        lat = float(0)
        if ret is not None:
            lng, lat = ret

        ack = terminal_packets.UploadStationAck(header.sn, lng, lat)
        yield self._send_res(conn_id, ack, pk.imei, peer)
        raise gen.Return(True)

    @gen.coroutine
    def _OnGpsSwitchReq(self, conn_id, header, body, peer):
        pk = terminal_packets.GPSSwtichReq()
        pk.Parse(body)
        str_pk = str(pk)
        self._OnOpLog('c2s header=%s body=%s peer=%s' % (header, body, peer),
                      pk.imei)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        logger.debug(
            "_OnGpsSwitchReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)

        ack = terminal_packets.GPSSwtichAck(header.sn, 1)
        yield self._send_res(conn_id, ack, pk.imei, peer)

        raise gen.Return(True)

    @gen.coroutine
    def _OnGetLocationReq(self, conn_id, header, body, peer):
        pk = terminal_packets.ReportLocationInfoReq()
        pk.Parse(body)
        str_pk = str(pk)

        logger.debug(
            "_OnGetLocationReq, parse packet success, pk=\"%s\" id=%u peer=%s",
            str_pk, conn_id, peer)
        self._broadcastor.register_conn(conn_id, pk.imei)
        self.imei_timer_mgr.add_imei(pk.imei)

        locator_time = pk.location_info.locator_time
        lnglat = []
        if pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_GPS:

            lnglat = [float(pk.location_info.longitude),
                      float(pk.location_info.latitude)]
        elif pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_STATION:
            ret = yield self.get_location_by_bts_info(
                pk.imei, pk.location_info.station_locator_data, None)
            if ret is not None:
                lnglat = ret
        elif pk.location_info.locator_status == terminal_packets.LOCATOR_STATUS_MIXED:

            ret = yield self.get_location_by_mixed(
                pk.imei, pk.location_info.station_locator_data, None,
                pk.location_info.mac)
            if ret is not None:
                lnglat = ret
        else:
            logger.warning("imei:%s location fail", pk.imei)
        self._OnOpLog('c2s header=%s pk=%s peer=%s' % (header, str_pk, peer),
                      pk.imei)
        if len(lnglat) != 0:
            location_info = {"lnglat": lnglat,
                             "locator_time": pk.location_info.locator_time}
            logger.info("imei:%s pk:%s location  lnglat:%s", pk, str_pk,
                        str(lnglat))
            yield self.new_device_dao.add_location_info(pk.imei, location_info)

        yield self.new_device_dao.update_device_info(
            pk.imei,
            status=pk.status,
            electric_quantity=pk.electric_quantity)

        pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid", "home_wifi", "common_wifi", "target_energy"),
                                                   device_imei=pk.imei)
        if pet_info is not None:
            sport_info = {}
            sport_info["diary"] = datetime.datetime.combine(datetime.date.today(),
                                                            datetime.time.min)
            sport_info["step_count"] = pk.step_count
            sport_info["distance"] = pk.distance
            sport_info["calorie"] = pk.calorie
            sport_info["target_energy"] = pet_info.get("target_energy",0)
            yield self.new_device_dao.add_sport_info(pk.imei, sport_info)
        raise gen.Return(True)

    @gen.coroutine
    def _SendPetInOrNotHomeMsg(self, imei, is_in_home):
        pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid", "pet_is_in_home"),
                                                   device_imei=imei)
        if pet_info is not None:
            uid = pet_info.get("uid", None)
            if uid is None:
                logger.warning("imei:%s uid not find", imei)
                return
            pet_is_in_home = pet_info["pet_is_in_home"]
            if (pet_is_in_home == 1 and is_in_home) or (pet_is_in_home == 0 and not is_in_home):
                return
            yield self.pet_dao.update_pet_info(pet_info["pet_id"], {"pet_is_in_home":1-pet_is_in_home})

            msg = push_msg.new_pet_not_home_msg()
            if is_in_home:
                msg = push_msg.new_pet_in_home_msg()
            try:
                yield self.msg_rpc.push_android(uids=str(uid),
                                                payload=msg,
                                                pass_through=1)
                yield self.msg_rpc.push_ios_useraccount(uids=str(uid),
                                            payload=msg)
            except Exception, e:
                logger.exception(e)

        else:
            logger.warning("imei:%s uid not find", imei)

    @gen.coroutine
    def _SendOnlineMsg(self, imei, battery, datetime):
        pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid"),
                                                   device_imei=imei)
        if pet_info is not None:
            uid = pet_info.get("uid", None)
            if uid is None:
                logger.warning("imei:%s uid not find", imei)
                return
            msg = push_msg.new_device_on_line_msg(battery, utils.date2str(datetime))
            try:
                yield self.msg_rpc.push_android(uids=str(uid),
                                                payload=msg,
                                                pass_through=1)
                yield self.msg_rpc.push_ios(uids=str(uid),
                                            payload=msg)
            except Exception, e:
                logger.exception(e)

        else:
            logger.warning("imei:%s uid not find", imei)

    @gen.coroutine
    def _OnImeiExpires(self, imeis):
        for imei in imeis:
            pet_info = yield self.pet_dao.get_pet_info(("pet_id", "uid"),
                                                       device_imei=imei)
            if pet_info is not None:
                uid = pet_info.get("uid", None)
                if uid is None:
                    logger.warning("imei:%s uid not find", imei)
                    continue
                msg = push_msg.new_device_off_line_msg()
                try:
                    yield self.msg_rpc.push_android(uids=str(uid),
                                                    payload=msg,
                                                    pass_through=1)
                    yield self.msg_rpc.push_ios(uids=str(uid),
                                                payload=msg)
                except Exception, e:
                    logger.exception(e)

            else:
                logger.warning("imei:%s uid not find", imei)

    @run_on_executor
    def get_location_by_bts_info(self, imei, bts_info, near_bts_infos):
        return get_location_by_bts_info(imei, bts_info, near_bts_infos)

    @run_on_executor
    def get_location_by_wifi(self, imei, macs):
        return get_location_by_wifi(imei, macs)

    @run_on_executor
    def get_location_by_mixed(self, imei, bts_info, near_bts_infos, macs):
        return get_location_by_mixed(imei, bts_info, near_bts_infos, macs)
