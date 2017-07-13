FROM ubuntu:14.04
MAINTAINER yawei:xdjm562@qq.com

ENV WORKDIR /data/mongodb

RUN mkdir $WORKDIR

RUN ubuntu_apt_config.sh

RUN apt-get install -y mongo-org

RUN create_key.sh mongo.key

RUN create_local_shard.sh

RUN init_super_user.sh default default

ENV PATHCREATEINDEX ../../src/lib/create_index.py

RUN python $PATHCREATEINDEX



