import pathlib
from enum import Enum
from typing import Optional

from src.pkg.errors import BadRequestError


class UnknownMimeTypeError(BadRequestError):
    pass

class ContentType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"
    TEXT = "text"
    
class MimeType(str, Enum):
    IMAGE_GIF = "image/gif"
    IMAGE_TIFF = "image/tiff"
    IMAGE_JPG = "image/jpg"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_BMP = "image/bmp"
    IMAGE_WEBP = "image/webp"
    PDF = "application/pdf"
    TEXT = "text/plain"

    @classmethod
    def parse(cls, content_type: str, file_name: Optional[str] = None) -> "MimeType":
        """Generates the mime type by handling issue from Middleware
        side with regards to content type and file name. It first tried to fi the content type
        directly, then tries to extract the second part of the content type and find a match in
        mime type, finally uses fine name to fit a mime type.

        Args:
            content_type (str): mime string of the file
            file_name (str; optional): file name. Defaults to None.

        Raises:
            ValueError: if nothing is found

        Returns:
            MimeType: the matching MimeType
        """
        try:
            return cls(content_type)
        except ValueError:
            pass

        try:
            return cls.new_from_extension(content_type.split("/")[-1])
        except UnknownMimeTypeError:
            pass

        if file_name is None:
            raise UnknownMimeTypeError

        file_extension = pathlib.Path(file_name).suffix.replace(".", "")
        return cls.new_from_extension(file_extension)

    @classmethod
    def new_from_extension(cls, extension: str) -> "MimeType":
        extension = extension.replace(".", "").lower()
        mapping = {
            "gif": cls.IMAGE_GIF,
            "tiff": cls.IMAGE_TIFF,
            "jpg": cls.IMAGE_JPG,
            "jpeg": cls.IMAGE_JPEG,
            "png": cls.IMAGE_PNG,
            "bmp": cls.IMAGE_BMP,
            "webp": cls.IMAGE_WEBP,
            "pdf": cls.PDF,
            "txt": cls.TEXT,
        }
        if extension in mapping:
            return mapping[extension]
        raise UnknownMimeTypeError

    def content_type(self) -> ContentType:
        if self in {
            MimeType.IMAGE_GIF,
            MimeType.IMAGE_JPG,
            MimeType.IMAGE_JPEG,
            MimeType.IMAGE_PNG,
            MimeType.IMAGE_BMP,
            MimeType.IMAGE_WEBP,
            MimeType.IMAGE_TIFF,
        }:
            return ContentType.IMAGE
        if self == MimeType.PDF:
            return ContentType.PDF
        if self == MimeType.TEXT:
            return ContentType.TEXT
        raise NotImplementedError
