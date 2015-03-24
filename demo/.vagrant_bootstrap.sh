#!/bin/bash

apt-get update
apt-get install -y redis-server git \
    python python-dev python-pip libxml2-dev libxslt-dev zlib1g-dev && \
    apt-get clean

pip install -r /mailer/requirements.txt

python l syncdb --noinput
python /mailer/manage.py migrate --noinput
python /mailer/manage.py loaddata /mailer/auth.json

/bin/bash -c 'python manage.py celeryd -Q default >& /dev/null & python /mailer/manage.py runserver 0.0.0.0:8000 >& /dev/null &'
