"""Parse local uploads; no external file services or executable formats."""

from io import BytesIO
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from fastapi import HTTPException

Image.MAX_IMAGE_PIXELS = 20_000_000


def validate_asset(data):
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(422, "Maximum file size is 10 MB")
    if data.startswith(b"%PDF-"):
        try:
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 500:
                raise ValueError()
            # PDFs are stored/downloaded as documents, never executed server-side.
            return "pdf", ".pdf"
        except Exception:
            raise HTTPException(
                422, "Upload a readable, unencrypted PDF with 1–500 pages"
            )
    try:
        with Image.open(BytesIO(data)) as image:
            fmt = image.format
            if fmt not in ("PNG", "JPEG", "WEBP"):
                raise ValueError()
            if image.width * image.height > 20_000_000:
                raise ValueError()
            image.verify()
        return "image", {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[fmt]
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        SyntaxError,
        Image.DecompressionBombError,
    ):
        raise HTTPException(
            422, "Upload a valid PNG, JPEG or WebP image (at most 20 megapixels)"
        )
