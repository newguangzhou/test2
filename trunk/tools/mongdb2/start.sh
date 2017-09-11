#!/bin/bash

if [ -z "$LAN_IP" ]; then
	echo "\$LAN_IP env not set"
	exit 1
fi

if [ -z "$1" ]; then
	echo "Please give listen port"
	exit 1
fi

if [ -z "$2" ]; then
	echo "Please give mongodb root path"
	exit 1
fi

DB_ROOT="/data/mongodb/db/$1"
if [ ! -d "$DB_ROOT" ]; then
	mkdir -p $DB_ROOT
fi

LOG_DIR="/data/mongodb/logs/$1"
if [ ! -d "$LOG_DIR" ]; then
	mkdir -p $LOG_DIR
fi

CMD_DIR=$2
PORT=$1
shift 2
$CMD_DIR/mongod --bind_ip $LAN_IP --port $PORT --logpath $LOG_DIR/mongodb.log --logRotate rename --dbpath $DB_ROOT --fork $*

