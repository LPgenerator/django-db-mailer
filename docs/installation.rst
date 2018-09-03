Installation
============

Compatibility
-------------

* Python: 2.7, pypy, 3.4, 3.5, 3.6, pypy3
* Django: 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 2.0


Installation
------------

Recommended way to install is via pip:

.. code-block:: bash

    $ pip install django-db-mailer

    # do not forget collect your project static on production servers
    $ python manage.py collectstatic


.. _basic:

Settings configuration
----------------------

Add ``dbmail`` and ``django.contrib.sites`` to ``INSTALLED_APPS`` in the settings.py:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django.contrib.sites',
        'dbmail',
        ...
    )
    SITE_ID = 1


DB initialization
-----------------

Create application tables on database:

.. code-block:: bash

    $ python manage.py syncdb


If you're using South:


.. code-block:: bash

    $ python manage.py migrate


**Important:** South 1.0 or greater is required to run this migrations.
