from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def get_private_storage():
    """Хранилище вне MEDIA_ROOT: файлы недоступны по прямой ссылке."""
    return FileSystemStorage(location=Path(settings.BASE_DIR) / "private_media")
