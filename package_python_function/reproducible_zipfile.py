from __future__ import annotations

import os
import shutil
import time
import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike
    from pathlib import Path
    from typing import Optional, Tuple, Union

DIR_MODE = 0o755
FILE_MODE = 0o644

class SourceDateEpochError(Exception):
    """Raise when there are issues with $SOURCE_DATE_EPOCH"""

def date_time() -> Tuple[int, int, int, int, int, int]:
    """Returns date_time value used to force overwrite on all ZipInfo objects. Defaults to
    1980-01-01 00:00:00. You can set this with the environment variable SOURCE_DATE_EPOCH as an
    integer value representing seconds since Epoch.
    """
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH", None)
    if source_date_epoch is not None:
        dt = time.gmtime(int(source_date_epoch))[:6]
        if dt[0] < 1980:
            raise SourceDateEpochError(
                "$SOURCE_DATE_EPOCH must be >= 315532800, since ZIP files need MS-DOS date/time format, which can be 1/1/1980, at minimum."
            )
        return dt
    return (1980, 1, 1, 0, 0, 0)

class ZipFile(zipfile.ZipFile):
    def write_reproducibly(
        self,
        filename: PathLike,
        arcname: Optional[Union[Path, str]] = None,
        compress_type: Optional[int] = None,
        compresslevel: Optional[int] = None,
    ):
        if not self.fp:
            raise ValueError("Attempt to write to ZIP archive that was already closed")
        if self._writing:
            raise ValueError("Can't write to ZIP archive while an open writing handle exists")

        zinfo = zipfile.ZipInfo.from_file(filename, arcname, strict_timestamps=self._strict_timestamps)
        zinfo.date_time = date_time()
        if zinfo.is_dir():
            zinfo.external_attr = (0o40000 | DIR_MODE) << 16
            zinfo.external_attr |= 0x10  # MS-DOS directory flag
        else:
            zinfo.external_attr = FILE_MODE << 16

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

    def writestr_reproducibly(
        self,
        zinfo_or_arcname: Union[str, zipfile.ZipInfo],
        data: Union[str, bytes],
        compress_type: Optional[int] = None,
        compresslevel: Optional[int] = None,
    ):
        if isinstance(data, str):
            data = data.encode("utf-8")

        if not isinstance(zinfo_or_arcname, zipfile.ZipInfo):
            zinfo = zipfile.ZipInfo(filename=zinfo_or_arcname, date_time=date_time())
            zinfo.compress_type = self.compression
            zinfo._compresslevel = self.compresslevel
            if zinfo.is_dir():
                zinfo.external_attr = (0o40000 | DIR_MODE) << 16
                zinfo.external_attr |= 0x10  # MS-DOS directory flag
            else:
                zinfo.external_attr = FILE_MODE << 16
        else:
            zinfo = zinfo_or_arcname

        zinfo.file_size = len(data)
        if compress_type is not None:
            zinfo.compress_type = compress_type

        if compresslevel is not None:
            zinfo._compresslevel = compresslevel

        if not self.fp:
            raise ValueError("Attempt to write to ZIP archive that was already closed")
        if self._writing:
            raise ValueError("Can't write to ZIP archive while an open writing handle exists.")

        with self._lock:
            with self.open(zinfo, mode="w") as dest:
                dest.write(data)
