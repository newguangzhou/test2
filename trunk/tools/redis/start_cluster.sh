#!/bin/bash

if [ -z "$LAN_IP" ]; then
	echo "\$LAN_IP env not set"
	exit 1
fi

if [ -z "$1" ]; then
	echo "Please give cluster ports, like this \"6379,6380\""
	exit 1
fi

if [ -z "$2" ]; then
	echo "Please give redis root path"
	exit 1
fi

if [ ! -f "$2/redis-server" ] || [ ! -f "$2/./redis-trib.rb" ]; then
	echo "Invalid redis root path"
	exit 1
fi

ports=$1 
ports=${ports//,/ }
nodes=""
for port in $ports 
do
	bash ./start_node.sh $port $2
	if [ "$?" != "0" ]; then
		exit 1
	fi
	nodes="$nodes $LAN_IP:$port"
done

$2/redis-trib.rb create --replicas 1 $nodes

