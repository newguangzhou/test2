#!/bin/bash

usage="port replset mongo_root [noauth]"

if [ -z "$LAN_IP" ]; then 
    echo "Not set \$LAN_IP env"
    exit 1
fi 

if [ -z "$1" ]; then 
    echo $usage
    exit 1
fi 

if [ -z "$2" ]; then 
    echo $usage
    exit 1
fi 

if [ -z "$3" ]; then 
    echo $usage
    exit 1
fi 

auth_opt="--keyFile ./cluster_key --clusterAuthMode keyFile"
if [ "$4" == "noauth" ]; then 
    auth_opt="--noauth"
else 
    if [ ! -f "./cluster_key" ]; then 
        echo "Cluster key not found"
        exit 1
    fi 
    chmod 600 ./cluster_key 
fi

port=$1
replset=$2
mongo_root=$3

LOG_DIR="/data/mongodb_logs/$port"
if [ ! -d "$LOG_DIR" ]; then 
    mkdir -p $LOG_DIR
    if [ "$?" != "0" ]; then 
        echo "Create log dir error"
        exit 1
    fi 
fi 

DATA_DIR="/data/mongodb_data/$port"
if [ ! -d "$DATA_DIR" ]; then 
    mkdir -p $DATA_DIR
    if [ "$?" != "0" ]; then 
        echo "Create data dir error"
        exit 1
    fi 
fi 

if [ -f "/proc/sys/net/core/somaxconn" ]; then 
	echo 600 > /proc/sys/net/core/somaxconn
fi 
if [ -f "/proc/sys/vm/overcommit_memory" ]; then 
	echo 1 > /proc/sys/vm/overcommit_memory 
fi 
if [ -f "/sys/kernel/mm/transparent_hugepage/enabled" ]; then 
	echo never > /sys/kernel/mm/transparent_hugepage/enabled 
fi 
if [ -f "/sys/kernel/mm/transparent_hugepage/defrag" ]; then 
    echo never > /sys/kernel/mm/transparent_hugepage/defrag 
fi 

$mongo_root/mongod --port $port --bind_ip $LAN_IP \
    --logpath "$LOG_DIR/mongodb.log" \
    --logappend \
    --fork \
    --dbpath "$DATA_DIR" \
    --directoryperdb \
    --wiredTigerDirectoryForIndexes \
    --shardsvr \
    $auth_opt \
    --replSet "$replset"
    

