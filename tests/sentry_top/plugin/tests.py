from exam import fixture

from sentry_top.plugin import TopPlugin, get_cluster

from sentry.models import Project
from sentry.testutils import TestCase


class BasePluginTest(TestCase):
    plugin_class = TopPlugin

    @fixture
    def plugin(self):
        return self.plugin_class()


class TopPluginTest(BasePluginTest):
    def setUp(self):
        self.client = get_cluster(hosts={0: {'db': 9}})
        self.client.flushdb()

    def test_simple(self):
        project_a = Project.objects.create(name='test 1')
        project_b = Project.objects.create(name='test 2')

        self.plugin.add_event(project_a)
        self.plugin.add_event(project_a)
        self.plugin.add_event(project_a)
        self.plugin.add_event(project_b)
        self.plugin.add_event(project_b)

        results = self.plugin.top_projects()
        assert results == [
            (project_a, 3),
            (project_b, 2),
        ]
