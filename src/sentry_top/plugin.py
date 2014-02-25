import sentry_top

from collections import defaultdict
from nydus.db import create_cluster
from time import time

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from sentry.models import Project
from sentry.plugins.base import Plugin


if not getattr(settings, 'SENTRY_TOP', None):
    raise ImproperlyConfigured('You need to configure SENTRY_TOP')


def get_cluster(hosts=None, router='nydus.db.routers.keyvalue.PartitionRouter'):
    if hosts is None:
        hosts = {
            0: {}  # localhost / default
        }

    return create_cluster({
        'engine': 'nydus.db.backends.redis.Redis',
        'router': router,
        'hosts': hosts,
    })

redis = get_cluster(**settings.SENTRY_TOP['redis'])

MINUTES = settings.SENTRY_TOP.get('total_minutes', 15)


class TopPlugin(Plugin):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry-top'
    version = sentry_top.VERSION
    description = 'Tracks active projects ala `top`'
    resource_links = [
        ('Bug Tracker', 'https://github.com/getsentry/sentry-top/issues'),
        ('Source', 'https://github.com/getsentry/sentry-top'),
    ]

    slug = 'top'
    title = 'Top'
    conf_title = title
    conf_key = 'top'

    def can_enable_for_projects(self):
        return False

    def add_event(self, project, client=redis):
        minute = int(time() / 60)
        keys = [
            # 'stop:e:{0}:{1}'.format(event.group_id),
            'stop:p:{0}'.format(minute),
        ]
        with client.map() as conn:
            for key in keys:
                conn.zincrby(key, project.id)
                conn.expire(key, (MINUTES + 1) * 60)

    def top_projects(self, minutes=15, num=100, client=redis):
        now = int(time() / 60)
        keys = []
        for minute in xrange(minutes):
            keys.append('stop:p:{0}'.format(now - minute))

        counts = []
        with client.map() as conn:
            for key in keys:
                counts.append(conn.zrevrange(key, 0, num, withscores=True))

        results = defaultdict(int)
        for countset in counts:
            for project_id, count in countset:
                results[int(project_id)] += int(count)

        sorted_results = sorted(
            results.items(), key=lambda x: x[1], reverse=True)[:num]

        project_map = dict(
            (p.id, p) for p in Project.objects.filter(id__in=[
                p_id for p_id, _ in sorted_results
            ]).select_related('team')
        )

        return [
            (project_map[p_id], c)
            for (p_id, c) in sorted_results
            if p_id in project_map
        ]

    def is_rate_limited(self, project):
        # TODO(dcramer): we need a way to hook into Sentry at event input
        # that guarantees this stat
        self.add_event(project)
