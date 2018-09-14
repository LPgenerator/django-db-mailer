#!/bin/bash

apt-get update
apt-get install -y redis-server git \
    python3 python3-pip python3-dev libxml2-dev libxslt-dev zlib1g-dev

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
export LANG=C.UTF-8

pip3 install --upgrade pip
pip3 install -r /mailer/requirements.txt

if [ -f "demo/db.sqlite" ]; then rm ./demo/db.sqlite; fi

python3 /mailer/manage.py migrate --noinput
python3 /mailer/manage.py loaddata /mailer/auth.json

nohup /bin/bash -c 'C_FORCE_ROOT=1 python3 /mailer/manage.py celeryd -Q default >& /dev/null & python3 /mailer/manage.py runserver 0.0.0.0:8000 >& /dev/null &' &
