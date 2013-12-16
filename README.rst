sentry-top
==========

An extension for Sentry which allows you to track the most active projects ala ``top``

Install
-------

Install the package via ``pip``::

    pip install sentry-top



Configuration
-------------

Configure ``SENTRY_TOP`` in your ``sentry.conf.py``:


::

    SENTRY_TOP = {
        'redis': {
            'hosts': {
                # for more information on configuring hosts, see the documentation for the
                # Nydus python package
                0: {
                    'host': 'localhost',
                    'port': 6379
                }
            }
        },
        'total_minutes': 15,
    }
