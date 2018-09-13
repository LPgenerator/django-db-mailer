FROM ubuntu:14.04
MAINTAINER gotlium <gotlium@gmail.com>

RUN apt-get update && apt-get install -y redis-server git \
    python python-dev python-pip libxml2-dev libxslt-dev zlib1g-dev && \
    apt-get clean

ADD ./demo/ /mailer

RUN pip install -r /mailer/requirements.txt

RUN python /mailer/manage.py migrate --noinput
RUN python /mailer/manage.py loaddata /mailer/auth.json

CMD /bin/bash -c 'C_FORCE_ROOT=1 python /mailer/manage.py celeryd -Q default >& /dev/null & redis-server >& /dev/null & python /mailer/manage.py runserver 0.0.0.0:8000'

EXPOSE 8000
