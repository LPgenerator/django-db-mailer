Providers examples
==================


Apple APNs/APNs2
----------------

.. code-block:: python

    send_db_push(
        'welcome',
        'device-token',
        {
            'name': 'User'
        },
        provider='dbmail.providers.apple.apns',

        # ios specific
        category='NEW_MESSAGE_CATEGORY',
        content_available=0,
        sound='default',
        badge=6
    )


Google GCM
----------

.. code-block:: python

    send_db_push(
        'welcome',
        'user-id',
        {
            'name': 'User'
        },
        provider='dbmail.providers.google.android',

        # android specific
        vibrationPattern=[2000, 1000, 500, 500],
        ledColor=[0, 0, 73, 31],
        priority=2,
        msgcnt=2,
        notId=121,
    )


Microsoft Tile
--------------

.. code-block:: python

    send_db_push(
        'welcome',
        'http://s.notify.live.net/u/1/sin/...',
        {
            'name': 'User'
        },
        provider='dbmail.providers.microsoft.tile',

        # MS specific
        template="tile",
        id="SecondaryTile.xaml?DefaultTitle=FromTile",
        count="5",
        back_background_image="http://background.com/back",
        background_image="http://background.images.com/background'",
        back_title="back title",
        back_content="back content here",
        event="title",  # instead title (configured on settings)
    )


Microsoft Toast
---------------

.. code-block:: python

    send_db_push(
        'welcome',
        'http://s.notify.live.net/u/1/sin/...',
        {
            'name': 'User'
        },
        provider='dbmail.providers.microsoft.toast',

        # MS specific
        sound='',
        param='/Page2.xaml?NavigatedFrom=Toast Notification',
        path='/Views/MainScreen.xaml',
        event="title",  # instead title (configured on settings)
    )


HTTP Push
---------

.. code-block:: python

    send_db_push(
        'welcome',
        'http://localhost/receiver/',
        {
            'name': 'User'
        },
        provider='dbmail.providers.http.push',

        # Not limited args
        event='registration',
        uid='12345',
    )


Centrifugo Push
---------------

.. code-block:: python

    send_db_push(
        'welcome',
        'users',
        {
            'name': 'User'
        },
        provider='dbmail.providers.centrifugo.push',

        # Not limited args
        event='registration',
        uid='12345',
    )


PushAll Service
---------------

.. code-block:: python

    send_db_push(
        'welcome',
        'broadcast',
        {
            'name': 'User'
        },
        provider='dbmail.providers.pushall.push',

        # Not limited args
        title='MyApp',
        # uid='12345',  # only for unicast
        # icon='example.com/icon.png',
        # url='example.com',
        # hidden=0,
        # encode='utf8',
        # priority=1,
        # ttl=86400,
    )
