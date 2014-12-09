.. _signals:

Signals
=======

Signals on database is a native Django signals.

Available variables for rules on Signals:

.. code-block:: html

    {{ date }} - current date
    {{ date_time }} - current datetime
    {{ site }} - current site
    {{ domain }} - current site domain
    {{ old_instance }} - old instance for pre_save
    {{ instance }} - instance from received signal
    {{ ... }} - all instance fields as vars

When all signals was configured, you need to reload your wsgi application.
Auto-reloading can be configured on settings by WSGI_AUTO_RELOAD/UWSGI_AUTO_RELOAD.
But if you launch application on several instances, do it manually.
