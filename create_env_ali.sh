#!/bin/bash

# Check system requires
for pk in gcc g++ libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk wget python-pip
do
    pk_path=`which $pk`
    if [ -z "$pk_path" ]; then
        echo "installing $pk "
	    apt-get install -y $pk
    fi
done

# Check python devel
if [ -z "`which python2-config`" ]; then
    echo "installing python-dev first"
    apt-get install -y python-dev
fi

# Check mongodb
# if [ -z "`which mongo`" ]; then
#    echo "installing mongodb first"
#    apt-get install -y mongodb-org
# fi



# Install requirements
if [ "`uname -s`" = "Darwin" ]; then
	pip install --trusted-host mirrors.aliyun.com -i http://mirrors.aliyun.com/pypi/simple/ -r ./requirements.txt
else
	pip install -i http://mirrors.aliyun.com/pypi/simple/ -r ./requirements.txt
fi





