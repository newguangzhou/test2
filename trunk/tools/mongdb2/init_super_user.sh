#!/bin/bash

usage="port username passwd mongodb_root"
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
	echo $usage
	exit 1
fi

port=$1
username=$2
passwd=$3
mongodir=$4

shift 4

eval_str="db.getMongo().getDB('admin').createUser({user:'${username}', pwd:'mgdb8w34asdadat51!((', roles:[{role:'readWriteAnyDatabase', db:'admin'}, {role:'userAdminAnyDatabase', db:'admin'}, {role:'clusterAdmin', db:'admin'}, {role:'dbAdminAnyDatabase', db:'admin'}]})"

$mongodir/mongo --host $LAN_IP --port $port $* --eval "$eval_str"


