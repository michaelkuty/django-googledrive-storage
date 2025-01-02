import glob
import os

from django.conf import settings
from django.core.files.storage import storages
from django.core.management.base import BaseCommand, CommandError

from gdstorage.storage import (GoogleDriveFilePermission,
                               GoogleDrivePermissionRole,
                               GoogleDrivePermissionType, GoogleDriveStorage)


class Command(BaseCommand):
    help = "Backup site to various storage formats"

    def add_arguments(self, parser):
        parser.add_argument("--database", action="store_true", default=False)
        parser.add_argument("--media", action="store_true", default=False)
        parser.add_argument("--update", action="store_true", default=True)
        parser.add_argument("--location-root", type=str)
        parser.add_argument("--location-db", type=str, default="db/")
        parser.add_argument("--location-media", type=str, default="media/")

    @property
    def storage(self):

        if not hasattr(self, "_storage"):
            self._storage = GoogleDriveStorage()
        return self._storage

    def _restore_db(self, *args, **options):

        db_path = self._get_path("db.sqlite3", "db")

        if not self.storage._check_file_exists(db_path):
            self.stdout.write(self.style.ERROR(f"File does not exists {db_path} - {response}"))

        response = self.storage._open(db_path)

        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            open(settings.DATABASES["default"]["NAME"], "wb+").write(response.read())

        self.stdout.write(self.style.SUCCESS(f"{response}"))
        self.stdout.write(self.style.SUCCESS("Successfully created backup of media folder."))

    def _get_path(self, name, prefix="db"):
        return os.path.join(settings.GOOGLE_DRIVE_STORAGE_MEDIA_ROOT, prefix, name)

    def _restore_folder(self, folder):

        media_path = os.path.join(settings.GOOGLE_DRIVE_STORAGE_MEDIA_ROOT, "media")
        directories, files = self.storage.listdir(folder)

        for directory in directories:
            local_dir = settings.MEDIA_ROOT + directory.replace(media_path, "")
            self.stdout.write(self.style.SUCCESS(f"Restoring {directory} -> {local_dir}."))
            try:
                os.makedirs(local_dir)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating {local_dir} - {e}"))

            self._restore_folder(directory)

        for file in files:
            try:
                local_path = settings.MEDIA_ROOT + file.replace(media_path, "")
                open(local_path, "wb+").write(self.storage._open(file).read())
                self.stdout.write(self.style.SUCCESS(f"Restoring {file} -> {local_path}."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error restoring {file} - {e}"))

    def _restore_media(self, *args, **options):

        media_path = os.path.join(settings.GOOGLE_DRIVE_STORAGE_MEDIA_ROOT, "media")

        self._restore_folder(media_path)
        self.stdout.write(self.style.SUCCESS("Successfully restored media folder."))

    def handle(self, *args, **options):
        self.options = options

        if options["database"]:
            self._restore_db(*args, **options)

        if options["media"]:
            self._restore_media(*args, **options)
