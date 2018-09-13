Installation for development
============================

Installation
------------

Install all required packages and configure your project and environment:

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
    $ ln -sf /bin/bash /bin/sh
    $ python manage.py runserver >& /dev/null &
    $ python manage.py celeryd -Q default >& /dev/null &
    $ python manage.py shell_plus --print-sql


Examples
--------
Simple test from command line:

.. code-block:: python

    >>> from dbmail.models import MailTemplate, MailGroup, MailGroupEmail, MailLog
    >>> from dbmail import send_db_mail

    >>> MailTemplate.objects.create(
            name="Site welcome template",
            subject="Welcome",
            message="Welcome to our site. We are glad to see you.",
            slug="welcome",
            is_html=False,
        )

    >>> group = MailGroup.objects.create(
            name="Site admins",
            slug="administrators",
        )
    >>> MailGroupEmail.objects.bulk_create([
            MailGroupEmail(name="Admin 1", email="admin1@example.com", group=group),
            MailGroupEmail(name="Admin 2", email="admin2@example.com", group=group),
        ])

    >>> # test simple string
    >>> send_db_mail('welcome', 'root@localhost')

    >>> # test emails list
    >>> send_db_mail('welcome', ['user1@example.com', 'user2@example.com'])

    >>> # test internal groups
    >>> send_db_mail('welcome', 'administrators')

    >>> # test without celery
    >>> send_db_mail('welcome', 'administrators', use_celery=False)

    >>> # Show what stored in logs
    >>> print MailLog.objects.all().count()


Make targets
------------
Simple shortcuts for fast development

| ``clean`` -  Clean temporary files
| ``clean-celery`` -  Clean all celery queues
| ``pep8`` -  Check code for pep8 rules
| ``sphinx`` -  Make app docs
| ``run`` -  Run Django development server
| ``run-celery`` -  Run celery daemon
| ``shell`` -  Run project shell
| ``run-redis`` -  Run Redis daemon
| ``help`` -  Display callable targets
