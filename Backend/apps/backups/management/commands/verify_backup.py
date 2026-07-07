from django.core.management.base import BaseCommand, CommandError

from apps.backups.models import BackupRun
from apps.backups.services import verify_backup


class Command(BaseCommand):
    help = 'Verify a backup bundle checksum.'

    def add_arguments(self, parser):
        parser.add_argument('backup_id', type=int)

    def handle(self, *args, **options):
        run = BackupRun.objects.filter(id=options['backup_id']).first()
        if not run:
            raise CommandError('Backup not found.')
        result = verify_backup(run)
        if not result['valid']:
            raise CommandError('Backup checksum verification failed.')
        self.stdout.write(self.style.SUCCESS(f"Backup #{run.id} verified."))
