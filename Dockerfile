FROM registry.cn-hangzhou.aliyuncs.com/ubuntu-14-04/ubuntu14.04
MAINTAINER yawei:xdjm562@qq.com

ENV WORKDIRROOT /data/server
ENV LOGDIR /data/logs
ENV USER_SRV_LOG /data/logs/user_srv_d/user_srv_d.log  # for tail to block container

RUN mkdir /data && \
    mkdir $WORKDIRROOT && \
    mkdir $LOGDIR && \
    mkdir $LOGDIR/user_srv_d && \
    touch $USER_SRV_LOG

WORKDIR $WORKDIRROOT

COPY . $WORKDIRROOT

USER root

RUN apt-get update && \
    sh ./create_env_ali.sh

ENV DOWNLOADS $WORKDIRROOT/downloads
ENV MIPUSHURL https://static.micloud.xiaomi.net/res/2d955a4f/other/MiPush_Server_Python_20170704.zip
ENV MIPUSHNAMEZIP ./MiPush_Server_Python_20170704.zip
ENV MIPUSHNAME ./xmpush-python-1.0.4

ENV TORNADOURL https://pypi.python.org/packages/source/t/tornado/tornado-4.2.tar.gz
ENV TORNADONAMEZIP ./tornado-4.2.tar.gz
ENV TORNADONAME ./tornado-4.2

RUN mkdir $DOWNLOADS && \
    cd $DOWNLOADS

RUN wget $TORNADOURL && \
    tar xvf $TORNADONAMEZIP

RUN cd $TORNADONAME && \
    python setup.py build && \
    python setup.py install && \
    cd ../
    # $DOWNLOADS


COPY xmpush-python-1.0.4  $DOWNLOADS

RUN cd $MIPUSHNAME && \
    python setup.py install

#
#WORKDIR $MIPUSHNAME
#
#RUN ls
#
#RUN python setup.py install

# clear
RUN cd ../../ && \
    rm -rf $DOWNLOADS

WORKDIR $WORKDIRROOT/trunk/src/appserver/apps/

CMD sh start_allserver_docker.sh && tail -f /data/logs/user_srv_d/user_srv_d.log


