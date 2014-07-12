Installation
============

Compatibility
-------------
* Python: 2.6, 2.7
* Django: 1.4, 1.5, 1.6


Recommended way to install is via pip::

  pip install django-db-mailer


.. _basic:

Basic
-----

* Add ``dbmail`` to ``INSTALLED_APPS`` in settings.py::

    INSTALLED_APPS = (
        ...
        'dbmail',
        ...
    )

* Create application tables on database::

    python manage.py syncdb

  If you're using South::

    python manage.py migrate

