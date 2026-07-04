from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Extract a backup bundle to a target directory for staging restore.'

    def add_arguments(self, parser):
        parser.add_argument('backup_id', type=int)
        parser.add_argument('--destination', required=True)

    def handle(self, *args, **options):
        call_command('restore_backup_bundle', options['backup_id'], destination=options['destination'])
