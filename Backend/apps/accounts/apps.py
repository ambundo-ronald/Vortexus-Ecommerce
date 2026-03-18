import logging
import shutil
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings
from django.contrib.staticfiles.finders import find

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        self._ensure_oscar_missing_image()

    def _ensure_oscar_missing_image(self):
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        missing_image_name = getattr(settings, 'OSCAR_MISSING_IMAGE_URL', 'image_not_found.jpg')
        if not media_root or not missing_image_name:
            return

        target_path = Path(media_root) / missing_image_name
        if target_path.exists():
            return

        source_path = find(f'oscar/img/{missing_image_name}')
        if not source_path:
            logger.warning('Oscar missing image source not found for %s', missing_image_name)
            return

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)
        except OSError as exc:  # pragma: no cover
            logger.warning('Could not copy Oscar missing image into MEDIA_ROOT: %s', exc)
