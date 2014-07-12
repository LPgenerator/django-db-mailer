Installation for development
============================

.. code-block:: bash

    $ apt-get install virtualenvwrapper redis-server
    $ mkvirtualenv django-db-mailer
    $ git clone https://github.com/LPgenerator/django-db-mailer.git
    $ cd django-db-mailer
    $ python setup.py develop
    $ cd demo
    $ pip install -r requirements.txt
    $ python manage.py syncdb
    $ python manage.py migrate
    $ redis-server >& /dev/null &
    $ cd ../
    $ make run_celery >& /dev/null &
    $ make run_shell


.. code-block:: python

    >>> from dbmail import send_db_mail
    >>> from dbmail.models import MailTemplate
    >>>
    >>> MailTemplate.objects.create(
            name="Site welcome template",
            subject="Welcome",
            message="Welcome to our site. We are glad to see you.",
            slug="welcome",
            is_html=False,
        )
    >>> # simple string
    >>> send_db_mail('welcome', 'root@localhost')
    >>> # list
    >>> send_db_mail('welcome', ['user1@example.com', 'user2@example.com'])
    >>> # internal groups
    >>> send_db_mail('welcome', 'administrators')
