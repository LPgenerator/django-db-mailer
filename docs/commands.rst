.. _commands:

Management commands
===================

Commands
--------
``send_dbmail_deferred_signal`` - Send deferred mails which stored on database (if dbmail.Signals was used).

``update_dbmail_cache`` - Best way for update cache after migration to new app version.

``clean_dbmail_cache`` - Clear all caches.

``clean_dbmail_logs`` - Clear old logs. Days can be defined as DB_MAILER_LOGS_EXPIRE_DAYS constant.

``dbmail_test_send`` - Send test mail from command line. For example:

.. code-block:: bash

    $ ./manage.py dbmail_test_send --email=root@local.host --pk=1 --without-celery


Crontab
-------

Simple example:

.. code-block:: bash

    SHELL=/bin/bash
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games
    MAILTO=root@localhost
    PYTHON_BIN=/home/user/example.com/venv/bin/python
    MANAGE_PY=/home/user/example.com/www/manage.py
    LOG_FILE=/var/log/dbmail.cron.log

    # Project commands
    30 2 * * * $PYTHON_BIN $MANAGE_PY clean_dbmail_logs >> $LOG_FILE 2>&1
