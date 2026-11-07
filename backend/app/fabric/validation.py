"""Upload validation and normalisation.

The *content* of the file is the authority, not its extension or the
client-declared MIME type, both of which are trivially spoofable.

After validation the image is re-encoded as an RGB JPEG. This:
  * strips EXIF metadata (including GPS location) before anything is stored,
  * applies EXIF orientation so the model and the user see the same picture,
  * caps the stored resolution, and
  * guarantees the bytes on disk are a well-formed image.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageOps, UnidentifiedImageError

# Pillow format name -> canonical label
ALLOWED_FORMATS = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

MIN_SIDE_PX = 64
MAX_INPUT_PIXELS = 40_000_000  # guards against decompression bombs
MAX_STORED_SIDE_PX = 2048
JPEG_QUALITY = 90


class ImageValidationError(Exception):
    """A user-correctable problem with an uploaded image.

    ``code`` is stable and machine readable; ``message`` is safe to show to
    end users (it never contains paths or stack traces).
    """

    def __init__(self, code: str, message: str, http_status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True)
class ValidatedImage:
    jpeg_bytes: bytes
    width: int
    height: int
    original_format: str
    sha256: str  # of the normalised bytes

    def to_pil(self) -> Image.Image:
        return Image.open(io.BytesIO(self.jpeg_bytes)).convert("RGB")


def check_declared_type(filename: Optional[str], content_type: Optional[str]) -> None:
    """Early, cheap rejection based on what the client *claims* to be sending.

    This is only a first filter. ``validate_and_normalize`` always inspects the
    real bytes.
    """
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        if ct not in ALLOWED_CONTENT_TYPES and ct != "application/octet-stream":
            raise ImageValidationError(
                "unsupported_format",
                "Unsupported file type. Please upload a JPG, JPEG, PNG or WEBP image.",
                415,
            )
    if filename and "." in filename:
        ext = "." + filename.rsplit(".", 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ImageValidationError(
                "unsupported_format",
                "Unsupported file extension. Please upload a JPG, JPEG, PNG or WEBP image.",
                415,
            )


def validate_and_normalize(
    data: bytes,
    *,
    max_bytes: int,
    min_side: int = MIN_SIDE_PX,
    max_pixels: int = MAX_INPUT_PIXELS,
    max_side: int = MAX_STORED_SIDE_PX,
) -> ValidatedImage:
    """Validate raw upload bytes and return a normalised, metadata-free JPEG."""
    if not data:
        raise ImageValidationError("empty_file", "The uploaded file is empty.")
    if len(data) > max_bytes:
        mb = max_bytes / (1024 * 1024)
        raise ImageValidationError(
            "file_too_large",
            f"The image is too large. The maximum size is {mb:.0f} MB.",
            413,
        )

    try:
        probe = Image.open(io.BytesIO(data))
        fmt = (probe.format or "").upper()
        width, height = probe.size  # header only; no full decode yet
    except UnidentifiedImageError:
        raise ImageValidationError(
            "unsupported_format",
            "That file is not a readable image. Please upload a JPG, PNG or WEBP photo.",
            415,
        )
    except (OSError, ValueError, Image.DecompressionBombError):
        raise ImageValidationError(
            "corrupt_image", "The image could not be read. It may be corrupted."
        )

    if fmt not in ALLOWED_FORMATS:
        raise ImageValidationError(
            "unsupported_format",
            "Unsupported image format. Please upload a JPG, JPEG, PNG or WEBP image.",
            415,
        )
    if width * height > max_pixels:
        raise ImageValidationError(
            "image_too_many_pixels",
            "The image resolution is too high to process. Please upload a smaller photo.",
            413,
        )
    if min(width, height) < min_side:
        raise ImageValidationError(
            "image_too_small",
            f"The image is too small. Both sides must be at least {min_side} pixels.",
        )

    try:
        # verify() consumes the file object, so decode from a fresh copy.
        Image.open(io.BytesIO(data)).verify()
        img = Image.open(io.BytesIO(data))
        img.load()
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.getchannel("A"))
            img = background
        else:
            img = img.convert("RGB")
        if max(img.size) > max_side:
            img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)  # no exif passed
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        raise ImageValidationError(
            "corrupt_image", "The image could not be read. It may be corrupted."
        )

    jpeg = out.getvalue()
    return ValidatedImage(
        jpeg_bytes=jpeg,
        width=img.size[0],
        height=img.size[1],
        original_format=ALLOWED_FORMATS[fmt],
        sha256=hashlib.sha256(jpeg).hexdigest(),
    )