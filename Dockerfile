FROM ubuntu:18.04
MAINTAINER gotlium <gotlium@gmail.com>

RUN apt-get update && apt-get install -y redis-server git \
    python3 python3-pip python3-dev libxml2-dev libxslt-dev zlib1g-dev && \
    apt-get clean

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

RUN mkdir /mailer
ADD . /mailer/
WORKDIR /mailer

RUN pip3 install --upgrade pip
RUN pip3 install -r /mailer/demo/requirements.txt
RUN pwd
# install dbmail from the local source
RUN python3 setup.py install

RUN python3 /mailer/demo/manage.py migrate --noinput
RUN python3 /mailer/demo/manage.py loaddata /mailer/demo/auth.json


CMD /bin/bash -c 'C_FORCE_ROOT=1 python3 /mailer/demo/manage.py celeryd -Q default >& /dev/null & redis-server >& /dev/null & python3 /mailer/demo/manage.py runserver 0.0.0.0:8000'

EXPOSE 8000
