import secrets
import io
import base64
import qrcode
from PIL import Image

def generate_secure_qr_token() -> str:
    """Generate a high-entropy cryptographically secure hex token for site QR."""
    return f"SITE-SEC-{secrets.token_hex(16).upper()}"

def generate_qr_code_base64(data: str) -> str:
    """Generate base64 encoded PNG data URI for a given QR payload."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"
