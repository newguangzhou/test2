# -*- coding: utf-8 -*-

import traceback
import sys
sys.path.append("../../")

reload(sys)
sys.setdefaultencoding("utf-8")

import time
import getopt
import signal
from tornado.ioloop import IOLoop
import tornado.options
import tornado
from tornado.options import define, options
from tornado.web import Application, url
from base import conn_mgr2
from base import broadcast
from lib.pyloader import PyLoader
from lib.op_log_dao import OPLogDAO
from lib.new_device_dao import NewDeviceDAO
from lib.pet_dao import PetDAO
from base import thread_trace
import terminal_handler
import http_handlers
support_setptitle = True
ptitle = "terminal_srv_d"
verbose = False
logrootdir = "./logs/"
listen_port = 5050
debug = False
http_listen_port = 5052
try:
    import setproctitle
except:
    support_setptitle = False

import logging

logger = logging.getLogger(__name__)
mongo_pyloader = PyLoader("configs.mongo_config")
mongo_conf = mongo_pyloader.ReloadInst("MongoConfig", debug_mode=debug)

# Parse options
#def Usage():
#   print "Usage:  -h  get help"
#   print "        -v  verbose"
#   print "        -t  process title, default is terminal_srv_d"
#   print "        -r  log root directory, default is ./logs/"
#   print "        -p  listen port, default is 9911"
#   print "        -d  Enable debug"

#opts = None
#try:
#   opts, args = getopt.getopt(sys.argv[1:], "hvt:r:p:d")
#except getopt.GetoptError, err:
#    print str(err)
#   Usage()
#    sys.exit(1)

#for o, a in opts:
#    if o == "-h":
#        Usage()
#        sys.exit()
#    elif o == "-v":
#        verbose = True
#    elif o == "-t":
#        ptitle = a
#   elif o == "-r":
#        logrootdir = a
#    elif o == "-p":
#        try:
#            listen_port = int(a)
#        except:
#            assert False, "Invalid listen port"
#    elif o == "-d":
#        debug = True
#    else:
#       assert False, "unhandled option"

# Init logger
#logdir = logrootdir
#if not logdir.endswith("/"):
#    logdir += "/"
#logdir += ptitle
#logger.Init(logdir, verbose, ptitle)

# Set process title
if support_setptitle:
    setproctitle.setproctitle(ptitle)
else:
    logger.warning(
        "System not support python setproctitle module, please check!!!")

# Init web application

if __name__ == '__main__':
    tornado.options.options.logging = "debug"
    tornado.options.parse_command_line()
    conn_mgr = conn_mgr2.ServerConnMgr()
    thread_trace.trace_start("trace.html")
    broadcastor = broadcast.BroadCastor(conn_mgr)

    # Create terminal server
    handler = terminal_handler.TerminalHandler(
        conn_mgr,
        debug,
        op_log_dao=OPLogDAO.new(mongo_meta=mongo_conf.op_log_mongo_meta),
        broadcastor=broadcastor,
        pet_dao=PetDAO.new(mongo_meta=mongo_conf.op_log_mongo_meta),
        new_device_dao=NewDeviceDAO.new(
            mongo_meta=mongo_conf.op_log_mongo_meta))

    conn_mgr.CreateTcpServer("", listen_port, handler)
    webapp = Application(
        [
            (r"/op_log", http_handlers.GetOpLogHandler),
            (r"/send_command", http_handlers.SendCommandHandler),
            (r"/send_command2", http_handlers.SendCommandHandler2),
            (r"/send_command3", http_handlers.SendCommandHandler3),
            (r"/send_command4", http_handlers.SendCommandHandler4),
            (r"/send_command_params", http_handlers.SendParamsCommandHandler),
            (r"/send_commandj03", http_handlers.SendCommandHandlerJ03),
            (r"/send_commandj13", http_handlers.SendCommandHandlerJ13),
        ],
        autoreload=True,
        debug=True,
        broadcastor=broadcastor,
        op_log_dao=OPLogDAO.new(mongo_meta=mongo_conf.op_log_mongo_meta), )
    webapp.listen(http_listen_port)
    IOLoop.instance().start()
# Init connection manager
#conn_mgr = conn_mgr.EpollConnMgr()

# Set signals
#def sig_handler(signum, frame):
#    try:
#        pass
#    except Exception, e:
#        logger.error(
#            "Clean error when siging, bug bug!!!, exp=\"%s\" trace=\"%s\"",
#            str(e), traceback.format_exc())
#    finally:
#        sys.exit(1)

#signal.signal(signal.SIGINT, sig_handler)
#signal.signal(signal.SIGTERM, sig_handler)

# Run loop
#while True:
#    try:
#        if not conn_mgr.CheckEvents(0.3, 1000):
#            break
#    except Exception, e:
#        logger.warning("Check events error, exp=\"%s\" trace=\"%s\"", str(e),
#                       traceback.format_exc())
