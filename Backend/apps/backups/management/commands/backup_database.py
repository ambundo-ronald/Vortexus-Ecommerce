from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create a database-only Vortexus backup bundle.'

    def handle(self, *args, **options):
        call_command('backup_site', backup_type='database')
