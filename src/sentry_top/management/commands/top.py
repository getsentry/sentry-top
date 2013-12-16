from django.core.management.base import BaseCommand
from optparse import make_option


class Command(BaseCommand):
    help = 'Reports the most active projects ala `top`.'

    option_list = BaseCommand.option_list + (
        make_option('--minutes', default='15', type=int, help='Number of minutes to check.'),
    )

    def handle(self, **options):
        from sentry.plugins import plugins

        plugin = plugins.get('top')
        for project, count in plugin.top_projects():
            print project.name, count
