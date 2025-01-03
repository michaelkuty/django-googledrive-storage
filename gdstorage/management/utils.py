import glob
import os

from django.conf import settings
from django.core.files.storage import storages
from django.core.management.base import BaseCommand, CommandError
from gdstorage.storage import (GoogleDriveFilePermission,
                               GoogleDrivePermissionRole,
                               GoogleDrivePermissionType, GoogleDriveStorage)


class CommandMixin:

    @property
    def storage(self):

        if not hasattr(self, "_storage"):
            if self.options.get("users") or hasattr(settings, "GOOGLE_DRIVE_STORAGE_DEFAULT_USER"):
                self._storage = GoogleDriveStorage(permissions=self.permissions)
            else:
                self._storage = GoogleDriveStorage()
        return self._storage

    def _get_path(self, name="db"):
        return os.path.join(settings.GOOGLE_DRIVE_STORAGE_MEDIA_ROOT, name)

    @property
    def users_to_share(self):
        return self.options.get("users") or settings.GOOGLE_DRIVE_STORAGE_DEFAULT_USER

    @property
    def permissions(self):
        return [
            GoogleDriveFilePermission(
                GoogleDrivePermissionRole.WRITER,
                GoogleDrivePermissionType.USER,
                self.options.get("users") or settings.GOOGLE_DRIVE_STORAGE_DEFAULT_USER,
            )
        ]

    def populate_permissions(self):
        # Setting up permissions

        file = self.storage._check_file_exists(settings.GOOGLE_DRIVE_STORAGE_MEDIA_ROOT)

        for p in self.permissions:
            if not file["permissions"][0]["emailAddress"] == self.users_to_share:
                self.storage.permissions().create(fileId=file["id"], body={**p.raw}).execute()
