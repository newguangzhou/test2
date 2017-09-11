#!/bin/bash

if [ -z "$LAN_IP" ]; then
	echo "\$LAN_IP env not set"
	exit 1
fi

if [ -z "$1" ]; then 
	echo "Please give redis listen port"
	exit 1
fi

if [ -z "$2" ]; then
	echo "Please give redis root path"
	exit 1
fi

LOG_DIR="/data/redis_logs/$1"
if [ ! -d "$LOG_DIR" ]; then 
	mkdir -p $LOG_DIR
	if [ "$?" != "0" ]; then 
		echo "Create log dir error"
		exit 1
	fi 
fi 

DATA_DIR="/data/redis_data/$1"
if [ ! -d "$DATA_DIR" ]; then 
	mkdir -p $DATA_DIR
	if [ "$?" != "0" ]; then 
		echo "Create data dir error"
		exit 1
	fi 
fi 

CONFIG_DIR="./configs"

if [ -f "/proc/sys/net/core/somaxconn" ]; then 
	echo 600 > /proc/sys/net/core/somaxconn
fi 
if [ -f "/proc/sys/vm/overcommit_memory" ]; then 
	echo 1 > /proc/sys/vm/overcommit_memory 
fi 
if [ -f "/sys/kernel/mm/transparent_hugepage/enabled" ]; then 
	echo never > /sys/kernel/mm/transparent_hugepage/enabled 
fi 

redis_config="include ./common.conf\n \
bind $LAN_IP\n \
port $1\n \
logfile $LOG_DIR/redis.log\n \
dir $DATA_DIR\n \
lua-time-limit 3000\n \
cluster-config-file cluster-$1.conf\n"

if [ ! -d "$CONFIG_DIR" ]; then 
	mkdir -p $CONFIG_DIR
fi
echo -e $redis_config  > $CONFIG_DIR/$1.conf

CWD=`pwd`

cd $CONFIG_DIR
$2/redis-server $1.conf

