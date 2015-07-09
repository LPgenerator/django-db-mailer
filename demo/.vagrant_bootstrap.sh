#!/bin/bash

apt-get update
apt-get install -y redis-server git \
    python python-dev python-pip libxml2-dev libxslt-dev zlib1g-dev

pip install -r /mailer/requirements.txt

if [ -f "demo/db.sqlite" ]; then rm ./demo/db.sqlite; fi

python /mailer/manage.py syncdb --noinput
python /mailer/manage.py migrate --noinput
python /mailer/manage.py loaddata /mailer/auth.json

nohup /bin/bash -c 'C_FORCE_ROOT=1 python /mailer/manage.py celeryd -Q default >& /dev/null & python /mailer/manage.py runserver 0.0.0.0:8000 >& /dev/null &' &
