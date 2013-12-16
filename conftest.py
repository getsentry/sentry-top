import os

from django.conf import settings


def pytest_configure(config):
    if not settings.configured:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'sentry.conf.server'

    settings.SENTRY_TOP = {
        'redis': {
            'hosts': {0: {'db': 9}},
        },
        'total_minutes': 15,
    }
