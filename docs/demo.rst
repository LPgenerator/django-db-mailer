.. _demo:

Demo installation
=================


Docker
------

.. code-block:: bash

    $ git clone --depth 1 -b master https://github.com/LPgenerator/django-db-mailer.git db-mailer
    $ cd db-mailer
    $ docker build -t dbmail .
    $ docker run -it -d -p 8000:8000 --name dbmail dbmail
    $ docker exec -i -t dbmail /bin/bash
    $ cd /mailer/


Vagrant
-------

.. code-block:: bash

    $ git clone --depth 1 -b master https://github.com/LPgenerator/django-db-mailer.git db-mailer
    $ cd db-mailer
    $ vagrant up --provider virtualbox
    $ vagrant ssh
    $ cd /mailer/


OS X/Linux
----------

.. code-block:: bash

    $ sudo apt-get install -y virtualenvwrapper redis-server git python-dev libxml2-dev libxslt-dev zlib1g-dev || brew install pyenv-virtualenvwrapper redis git
    $ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh || source /usr/local/bin/virtualenvwrapper.sh
    $ mkvirtualenv db-mailer
    $ workon db-mailer
    $ git clone --depth 1 https://github.com/LPgenerator/django-db-mailer.git db-mailer
    $ cd db-mailer
    $ python setup.py develop
    $ cd demo
    $ pip install -r requirements.txt
    $ python manage.py migrate --noinput
    $ python manage.py createsuperuser --username admin --email admin@local.host
    $ redis-server >& /dev/null &
    $ python manage.py runserver >& /dev/null &
    $ python manage.py celeryd -Q default >& /dev/null &


Demo scenario
-------------

Open Shell:

.. code-block:: bash

    $ python manage.py shell_plus --print-sql


Create new template:

.. code-block:: python

    from dbmail.models import MailTemplate
    from dbmail import send_db_mail

    MailTemplate.objects.create(
        name="Site welcome template",
        subject="Welcome",
        message="Welcome to our site. We are glad to see you.",
        slug="welcome",
        is_html=False,
    )


Try to send test email with created template (without celery):

.. code-block:: python

    send_db_mail('welcome', 'user@example.com', use_celery=False)


Send email using celery:

.. code-block:: python

    send_db_mail('welcome', 'user@example.com')


Check mail logs:

.. code-block:: python

    from pprint import pprint
    from django.forms.models import model_to_dict
    from dbmail.models import MailLog

    pprint([model_to_dict(obj) for obj in MailLog.objects.all()])


Open app in browser (login and password is admin/admin):

.. code-block:: bash

    $ xdg-open http://127.0.0.1:8000/admin/dbmail/ >& /dev/null || open http://127.0.0.1:8000/admin/dbmail/ >& /dev/null
