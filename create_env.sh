#!/bin/bash

ENV_DIR="`pwd`/pyenv"

# Check system requires
for pk in gcc g++ virtualenv
do
    pk_path=`which $pk`
    if [ -z "$pk_path" ]; then
        echo "Please install -y $pk first"
        exit 1
    fi
done

# Check python devel
if [ -z "`which python2-config`" ]; then
    echo "Please install python2 devel first"
    exit 1
fi

# Check env directory
if [ -d "$ENV_DIR" ]; then
    read -p "Warning, virtualenv directory \"${ENV_DIR}\" already exist, are you sure to delete it?(yes/no)" res
    if [ "$res" = "no" ]; then
        echo "Cancel"
        exit 1
    elif [ "$res" != "yes" ]; then
        echo "Invalid input"
        exit 1
    fi
    rm -fr $ENV_DIR
fi

# create virtualenv
virtualenv $ENV_DIR
if [ "$?" != "0" ]; then
   echo "Create virtualenv failed!"
   exit 1
fi

# Active virtualenv
source ./pyenv/bin/activate
if [ "$?" != "0" ]; then
   echo "Active virtualenv failed!"
   exit 1
fi

# Install requirements
if [ "`uname -s`" = "Darwin" ]; then
	pip install --trusted-host mirrors.aliyun.com -i http://mirrors.aliyun.com/pypi/simple/ -r ./requirements.txt
else
	pip install -i http://mirrors.aliyun.com/pypi/simple/ -r ./requirements.txt
fi



