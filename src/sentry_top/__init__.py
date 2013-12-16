try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('sentry-top').version
except Exception, e:
    VERSION = 'unknown'
