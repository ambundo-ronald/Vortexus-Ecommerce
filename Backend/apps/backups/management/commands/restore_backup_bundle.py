from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.backups.models import BackupRun
from apps.backups.services import restore_backup_to_directory


class Command(BaseCommand):
    help = 'Extract a backup bundle to a target directory for staging restore.'

    def add_arguments(self, parser):
        parser.add_argument('backup_id', type=int)
        parser.add_argument('--destination', required=True)

    def handle(self, *args, **options):
        run = BackupRun.objects.filter(id=options['backup_id']).first()
        if not run:
            raise CommandError('Backup not found.')
        try:
            result = restore_backup_to_directory(run, Path(options['destination']))
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Backup #{run.id} extracted to {result['destination']}."))
