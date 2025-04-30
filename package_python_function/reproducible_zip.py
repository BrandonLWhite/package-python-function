from __future__ import annotations

import os
import shutil
import time
from copy import copy
from typing import TYPE_CHECKING
from zipfile import ZipFile, ZipInfo

if TYPE_CHECKING:
    from typing import Tuple

FILE_MODE = 0o644
DIR_MODE = 0o755

def date_time() -> Tuple[int, int, int, int, int, int]:
    """Returns date_time value used to force overwrite on all ZipInfo objects. Defaults to
    1980-01-01 00:00:00. You can set this with the environment variable SOURCE_DATE_EPOCH as an
    integer value representing seconds since Epoch.
    """
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH", None)
    if source_date_epoch is not None:
        return time.gmtime(int(source_date_epoch))[:6]
    return (1980, 1, 1, 0, 0, 0)

def clean_zip_info(zinfo: ZipInfo) -> ZipInfo:
    """
    Cleans the ZipInfo object, overwriting file-modified timestamps and file/directory permissions modes in write mode in order to create a reproducible ZIP archive.

    Parameters:
    zinfo (ZipInfo): A ZipInfo object from zipfile.ZipInfo.

    Returns:
    ZipInfo: The ZipInfo for the file, with the proper file permissions and date.
    """
    zinfo = copy(zinfo)
    zinfo.date_time = date_time()
    if zinfo.is_dir():
        zinfo.external_attr = (0o40000 | DIR_MODE) << 16
        zinfo.external_attr |= 0x10  # MS-DOS directory flag
    else:
        zinfo.external_attr = FILE_MODE << 16
    return zinfo

class ReproducibleZipFile(ZipFile):
    """Open a ZIP file, where file can be a path to a file (a string), a file-like object or a
    path-like object.

    This is a replacement for the Python standard library zipfile.ZipFile that overwrites
    file-modified timestamps and file/directory permissions modes in write mode in order to create
    a reproducible ZIP archive.
    """

    # Following method modified from Python 3.12.9
    # https://github.com/python/cpython/blob/fdb81425a9ad683f8c24bf5cbedc9b96baf00cd2/Lib/zipfile/__init__.py#L1834-L1865
    # Copyright Python Software Foundation, licensed under PSF License Version 2
    # See LICENSE file for full license agreement and notice of copyright
    def write(self, filename, arcname=None, compress_type=None, compresslevel=None):
        """Put the bytes from filename into the archive under the name
        arcname."""
        if not self.fp:
            raise ValueError("Attempt to write to ZIP archive that was already closed")
        if self._writing:
            raise ValueError("Can't write to ZIP archive while an open writing handle exists")

        zinfo = ZipInfo.from_file(filename, arcname, strict_timestamps=self._strict_timestamps)

        ###### BEGIN ADDED CODE ######
        zinfo = clean_zip_info(zinfo)
        ###### END ADDED CODE ######

        if zinfo.is_dir():
            zinfo.compress_size = 0
            zinfo.CRC = 0
            self.mkdir(zinfo)
        else:
            if compress_type is not None:
                zinfo.compress_type = compress_type
            else:
                zinfo.compress_type = self.compression

            if compresslevel is not None:
                zinfo._compresslevel = compresslevel
            else:
                zinfo._compresslevel = self.compresslevel

            with open(filename, "rb") as src, self.open(zinfo, "w") as dest:
                shutil.copyfileobj(src, dest, 1024 * 8)
