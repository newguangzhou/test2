FROM registry.cn-hangzhou.aliyuncs.com/ubuntu-14-04/ubuntu14.04
MAINTAINER yawei:xdjm562@qq.com

ENV MONGODIR /data/mongodb

USER root

RUN mkdir /data $MONGODIR $MONGODIR/scripts

COPY . $MONGODIR/scripts

WORKDIR $MONGODIR/scripts

RUN sh ubuntu_apt_config.sh  # add mongo-org3.0 into apt list

RUN apt-get install -y mongodb-org

RUN apt-get install -y python-pip

RUN pip install pymongo

RUN sh create_key.sh mongo.key #generate base64 key by openssl

COPY create_local_shard_docker.sh /usr/bin/create_local_shard_docker

# create repl set and tail log to avoid container exit
CMD sh create_local_shard_docker.sh && tail -f /data/mongodb/logs/mongo_shard1_27020/mongod.log

#CMD sh create_local_shard_docker.sh

#RUN sh init_super_user_input.sh yawei admin
#
#RUN sh init_super_user.sh default default
#
#COPY ../../src/appserver/lib $MONGODIR/scripts
#
#ENV PATHCREATEINDEX ./lib/create_index.py
#
#RUN python $PATHCREATEINDEX



