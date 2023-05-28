# -*- coding: UTF-8 -*-
import tempfile
from pathlib import Path
from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from qcloud_cos import CosConfig, CosS3Client


@deconstructible()
class QcloudStorage(Storage):
    def __init__(self, option=None):
        if not option:
            self.option = settings.QCLOUD_STORAGE_OPTION
        else:
            self.option = option
        self.config = CosConfig(Region=self.option['Region'], SecretId=self.option['SecretId'],
                                SecretKey=self.option['SecretKey'], Token=self.option.get('Token'))
        self.bucket = self.option['Bucket']

    def _check_url(self, name):
        return name.startswith('http')

    def _open(self, name, mode='rb'):
        if self._check_url(name):
            return b''

        client = CosS3Client(self.config)
        response = client.get_object(self.bucket, name)
        tmpf = Path(tempfile.gettempdir(), name)
        parent = tmpf.parent
        if not parent.exists():
            parent.mkdir(parents=True)
        response['Body'].get_stream_to_file(tmpf)
        return open(tmpf, mode)

    def _save(self, name, content):
        if self._check_url(name):
            return name

        client = CosS3Client(self.config)
        _ = client.put_object(self.bucket, content, name)
        return name

    def exists(self, name):
        if not name:
            return False
        if self._check_url(name):
            return True

        client = CosS3Client(self.config)
        response = client.object_exists(self.bucket, name)
        return response

    def url(self, name):
        if self._check_url(name):
            return name

        if getattr(settings, 'COS_URL', ''):
            url = "{}/{}".format(settings.COS_URL, name)
        elif getattr(settings, 'COS_FAST_CDN', False):
            url = "https://{}.file.myqcloud.com/{}".format(
                self.bucket, name)
        else:
            url = "https://{}.cos.{}.myqcloud.com/{}".format(
                self.bucket, self.option['Region'], name
            )

        return url

    def size(self, name):
        if self._check_url(name):
            return 0

        client = CosS3Client(self.config)
        response = client.head_object(self.bucket, name)
        return response['Content-Length']

    def delete(self, name):
        if self._check_url(name):
            return

        client = CosS3Client(self.config)
        client.delete_object(self.bucket, name)


class PrefixedQcloudStorage(QcloudStorage):

    def __init__(self, option=None, prefix=""):
        super().__init__(option=option)
        self.prefix = prefix

    def _alter_name(self, name):
        if self._check_url(name):
            return name
        return f"{self.prefix}/{name}"

    def size(self, name):
        name = self._alter_name(name)
        return super().size(name)

    def delete(self, name):
        name = self._alter_name(name)
        return super().delete(name)

    def url(self, name):
        name = self._alter_name(name)
        return super().url(name)

    def exists(self, name):
        name = self._alter_name(name)
        return super().exists(name)

    def _open(self, name, mode='rb'):
        name = self._alter_name(name)
        return super()._save(name, mode)

    def _save(self, name, content):
        name = self._alter_name(name)
        return super()._save(name, content)

    @classmethod
    def get_relative_location(cls, location):
        """get relative location for OSS storage. since Django requires settings.MEDIA_ROOT and settings.STATIC_ROOT
        to be absolute paths, we provide this method to calculate the essential relative path.
        Most of the case there is a BASE_DIR or ROOT_DIR setting as the root directory of the project, we calculate
        relative path based on these two settings if they exist."""
        base_dir = None
        location = str(location)
        if hasattr(settings, "BASE_DIR"):           #
            base_dir = str(settings.BASE_DIR)
        elif hasattr(settings, "ROOT_DIR"):
            base_dir = str(settings.ROOT_DIR)
        if base_dir is None:
            return location
        if not location.startswith(base_dir):
            return location
        return location[len(base_dir):]

    @classmethod
    def strip_splash(cls, location):
        if location.startswith('/'):
            return location[1:]
        return location


class QcloudMediaStorage(PrefixedQcloudStorage):

    def __init__(self, option=None):
        prefix = super().strip_splash(
            super().get_relative_location(settings.MEDIA_ROOT)
        )
        super().__init__(option=option, prefix=prefix)


class QcloudStaticStorage(PrefixedQcloudStorage):

    def __init__(self, option=None):
        prefix = super().strip_splash(
            super().get_relative_location(settings.STATIC_ROOT)
        )
        super().__init__(option=option, prefix=prefix)

