#!/bin/bash

if [ -z "$1" ]; then
	echo "Please give a file name"
	exit 1
fi

openssl rand -base64 741 > $1

chmod 600 $1

