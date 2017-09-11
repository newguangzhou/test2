#!/bin/bash

#set -x 

if [ -z "$LAN_IP" ]; then
	echo "Please set \$LAN_IP env"
	exit 1
fi

usage="peer_port client_port cluster_nodes etcd_root"

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
	echo $usage
	exit 1
fi

peer_port=$1
client_port=$2
all_nodes=$3
etcd_root=$4

node_name="node_${LAN_IP//./_}_$peer_port"

cluster_nodes=""
for node in ${all_nodes//,/ } 
do
	tmp1=`echo $node | cut -d':' -f1`
	ip=${tmp1//./_}
	port=`echo $node| cut -d':' -f2`
	name="node_${ip}_${port}"
	if [ ! -z "$cluster_nodes" ]; then 
		cluster_nodes="${cluster_nodes},${name}=http://${node}"
	else 
		cluster_nodes="${name}=http://${node}"
	fi
done 

data_root="/data/etcd_data/${node_name}"
#data_root="./etcd_data/${node_name}"
if [ ! -d "$data_root" ]; then 
	mkdir -p $data_root
	if [ "$?" != "0" ]; then 
		echo "Create data root error"
		exit 1
	fi
fi 

log_root="/data/etcd_logs/${node_name}"
#log_root="./etcd_logs/${node_name}"
if [ ! -d "$log_root" ]; then
	mkdir -p $log_root
	if [ "$?" != "0" ]; then 
		echo "Create log root error"
		exit 1
	fi
fi

shift 4

nohup $etcd_root/etcd --name "${node_name}" \
	--initial-advertise-peer-urls "http://$LAN_IP:$peer_port" \
	--listen-peer-urls "http://$LAN_IP:$peer_port" \
	--listen-client-urls "http://$LAN_IP:$client_port" \
	--advertise-client-urls "http://$LAN_IP:$client_port" \
	--initial-cluster-token "xmq_etcd_cluster" \
	--initial-cluster "${cluster_nodes}" \
	--data-dir "${data_root}" \
	--initial-cluster-state new >> "$log_root/etcd.log" 2>&1 &

