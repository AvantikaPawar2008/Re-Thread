"""Upload validation: formats, sizes, corrupt files, metadata stripping."""

import io

import pytest
from PIL import Image

from backend.app.fabric.validation import (
    ImageValidationError,
    check_declared_type,
    validate_and_normalize,
)

MAX = 8 * 1024 * 1024


def _img_bytes(fmt="JPEG", size=(200, 160), mode="RGB", color=(120, 160, 110), **save_kwargs):
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_accepts_supported_formats(fmt):
    result = validate_and_normalize(_img_bytes(fmt), max_bytes=MAX)
    assert result.original_format == fmt.lower()
    assert (result.width, result.height) == (200, 160)
    # Always re-encoded as JPEG
    assert Image.open(io.BytesIO(result.jpeg_bytes)).format == "JPEG"
    assert len(result.sha256) == 64


def test_rejects_empty():
    with pytest.raises(ImageValidationError) as e:
        validate_and_normalize(b"", max_bytes=MAX)
    assert e.value.code == "empty_file"


def test_rejects_too_large():
    with pytest.raises(ImageValidationError) as e:
        validate_and_normalize(_img_bytes(), max_bytes=100)
    assert e.value.code == "file_too_large"
    assert e.value.http_status == 413


def test_rejects_non_image_bytes():
    with pytest.raises(ImageValidationError) as e:
        validate_and_normalize(b"%PDF-1.4 this is not an image", max_bytes=MAX)
    assert e.value.code == "unsupported_format"


def test_rejects_unsupported_real_format_even_if_named_jpg():
    gif = _img_bytes("GIF")
    with pytest.raises(ImageValidationError) as e:
        validate_and_normalize(gif, max_bytes=MAX)
    assert e.value.code == "unsupported_format"


def test_rejects_truncated_image():
    data = _img_bytes("PNG", size=(300, 300))
    with pytest.raises(ImageValidationError) as e:
        validate_and_normalize(data[: len(data) // 2], max_bytes=MAX)
    assert e.value.code == "corrupt_image"


def test_rejects_tiny_image():
    with pytest.raises(ImageValidationError) as e:
        validate_and_normalize(_img_bytes(size=(20, 20)), max_bytes=MAX)
    assert e.value.code == "image_too_small"


def test_rejects_too_many_pixels():
    with pytest.raises(ImageValidationError) as e:
        validate_and_normalize(_img_bytes(size=(300, 300)), max_bytes=MAX, max_pixels=1000)
    assert e.value.code == "image_too_many_pixels"


def test_transparent_png_is_flattened_on_white():
    data = _img_bytes("PNG", mode="RGBA", color=(0, 0, 0, 0))
    out = validate_and_normalize(data, max_bytes=MAX).to_pil()
    r, g, b = out.getpixel((10, 10))
    assert min(r, g, b) > 240  # transparent -> white, not black


def test_large_images_are_downscaled():
    data = _img_bytes(size=(3000, 1500))
    out = validate_and_normalize(data, max_bytes=MAX, max_side=1024)
    assert max(out.width, out.height) == 1024


def test_exif_is_stripped_and_orientation_applied():
    img = Image.new("RGB", (200, 100), (10, 200, 10))
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees CW when displayed
    exif[0x010F] = "SecretCameraMake"
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    out = validate_and_normalize(buf.getvalue(), max_bytes=MAX)
    # orientation applied: 200x100 becomes 100x200
    assert (out.width, out.height) == (100, 200)
    stored = Image.open(io.BytesIO(out.jpeg_bytes))
    assert len(stored.getexif()) == 0
    assert b"SecretCameraMake" not in out.jpeg_bytes


@pytest.mark.parametrize(
    "filename,ctype",
    [("fabric.jpg", "image/jpeg"), ("fabric.PNG", "image/png"), ("x.webp", "image/webp"), ("blob", None)],
)
def test_declared_type_accepts(filename, ctype):
    check_declared_type(filename, ctype)


@pytest.mark.parametrize(
    "filename,ctype",
    [("a.gif", "image/gif"), ("a.pdf", "application/pdf"), ("a.exe", "application/octet-stream"), ("a.svg", "image/svg+xml")],
)
def test_declared_type_rejects(filename, ctype):
    with pytest.raises(ImageValidationError) as e:
        check_declared_type(filename, ctype)
    assert e.value.code == "unsupported_format"
    assert e.value.http_status == 415