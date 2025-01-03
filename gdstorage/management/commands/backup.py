import glob
import os

from django.conf import settings
from django.core.files.storage import storages
from django.core.management.base import BaseCommand, CommandError
from gdstorage.management.utils import CommandMixin
from gdstorage.storage import (GoogleDriveFilePermission,
                               GoogleDrivePermissionRole,
                               GoogleDrivePermissionType, GoogleDriveStorage)


class Command(BaseCommand, CommandMixin):
    help = "Backup site to various storage formats"

    def add_arguments(self, parser):
        # parser.add_argument("dry-run", nargs="+", type=bool)
        parser.add_argument("--users", type=str)
        parser.add_argument("--database", action="store_true", default=False)
        parser.add_argument("--media", action="store_true", default=False)
        parser.add_argument("--update", action="store_true", default=True)
        parser.add_argument("--location-root", type=str)
        parser.add_argument("--location-db", type=str, default="db/")
        parser.add_argument("--location-media", type=str, default="media/")

    def _backup_db(self, *args, **options):

        db_conf = settings.DATABASES["default"]

        if db_conf["ENGINE"] == "django.db.backends.sqlite3":
            fp = open(db_conf["NAME"], "rb")

            response = self.storage.save(
                os.path.join(self._get_path("db"), str(db_conf["NAME"]).split("/")[-1]),
                content=fp,
                update=options["update"],
            )

            self.stdout.write(self.style.SUCCESS(f"{response}"))
            self.stdout.write(self.style.SUCCESS("Successfully created backup of media folder."))
        else:
            self.stdout.write(self.style.SUCCESS("DB Engine not supported now."))

    def _backup_media(self, *args, **options):

        # Use glob to find all files in all directories
        all_files = glob.glob(
            os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, "**", "*.*"), recursive=True
        )

        # Print the list of files
        for file in all_files:
            filename = self._get_path("media") + os.path.join(
                file.replace(str(settings.MEDIA_ROOT), "")
            )
            self.stdout.write(self.style.SUCCESS(f"{file} -> {filename}"))

            response = self.storage.save(
                filename,
                content=open(file, "rb"),
                update=options["update"],
            )

            self.stdout.write(self.style.SUCCESS(f"{response}"))

        self.stdout.write(self.style.SUCCESS("Successfully created backup of media folder."))

    def handle(self, *args, **options):
        self.options = options

        self.populate_permissions()
        if options["database"]:
            self._backup_db(*args, **options)

        if options["media"]:
            self._backup_media(*args, **options)
