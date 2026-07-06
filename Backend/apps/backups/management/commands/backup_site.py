from django.core.management.base import BaseCommand, CommandError

from apps.backups.models import BackupRun
from apps.backups.services import create_backup, serialize_backup_run


class Command(BaseCommand):
    help = 'Create a Reesolmart backup bundle.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=[BackupRun.TYPE_FULL, BackupRun.TYPE_DATABASE, BackupRun.TYPE_MEDIA],
            default=BackupRun.TYPE_FULL,
            dest='backup_type',
        )

    def handle(self, *args, **options):
        try:
            run = create_backup(backup_type=options['backup_type'])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Backup #{run.id} completed: {serialize_backup_run(run)['storage_path']}"))
