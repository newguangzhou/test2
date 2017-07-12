FROM registry.cn-hangzhou.aliyuncs.com/ubuntu-14-04/ubuntu14.04
MAINTAINER yawei:xdjm562@qq.com

ENV WORKDIR /data/server
ENV LOGDIR /data/logs

RUN mkdir /data && \
    mkdir $WORKDIR && \
    mkdir $LOGDIR

WORKDIR $WORKDIR

COPY . $WORKDIR

USER root

RUN apt-get update && \
    sh ./create_env_ali.sh

ENV DOWNLOADS ./downloads
ENV MIPUSHURL https://static.micloud.xiaomi.net/res/2d955a4f/other/MiPush_Server_Python_20170704.zip
ENV MIPUSHNAMEZIP ./MiPush_Server_Python_20170704.zip
ENV MIPUSHNAME ./MiPush_Server_Python_20170704

RUN mkdir $DOWNLOADS && \
    cd $DOWNLOADS


RUN wget $MIPUSHURL

ADD $MIPUSHNAMEZIP .

RUN cd $MIPUSHNAME && \
    python setup.py install

RUN cd ../../trunk/src/appserver/apps/

CMD ["start_allserver.sh"]


