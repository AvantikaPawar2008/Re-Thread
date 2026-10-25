"""QR Code Generation using the Python qrcode library.

Generates unique recommendation identifiers and standard QR images
encoded as base64 data URIs for partner intake scanning.
"""

import base64
import io
import uuid
import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generate_qr_id() -> str:
    """Generate a unique lifecycle QR code identifier."""
    return f"rt-{uuid.uuid4().hex[:8]}"


def generate_qr_base64(qr_id: str) -> str:
    """Generate a PNG QR code for a recommendation ID, encoded as base64 data URI."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    # The QR payload contains a deep-link URI
    payload = f"rethread://outcome/{qr_id}"
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"
