#!/bin/bash

if [ -z "$LAN_IP" ]; then
	echo "\$LAN_IP env not set"
	exit 1
fi

if [ -z "$1" ]; then
	echo "Please give etcd root path"
	exit 1
fi

$1/etcd --listen-peer-urls "http://$LAN_IP:2380, http://$LAN_IP:7001" --listen-client-urls "http://$LAN_IP:2379, http://$LAN_IP:4001" --advertise-client-urls="http://$LAN_IP:2379, http://$LAN_IP:4001" 

