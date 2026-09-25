import io
from typing import Tuple, Dict, Any
from PIL import Image

ALLOWED_MIME_TYPES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/jpg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"]
}

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
MIN_IMAGE_DIMENSION = 200 # Minimum 200x200 pixels

def sniff_mime_type(file_bytes: bytes) -> str:
    """Detect MIME type by checking magic bytes rather than trusting client headers"""
    for mime, magic_signatures in ALLOWED_MIME_TYPES.items():
        for sig in magic_signatures:
            if file_bytes.startswith(sig):
                return "image/jpeg" if "jpeg" in mime or "jpg" in mime else "image/png"
    return "unknown"

def validate_image_file(file_bytes: bytes, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates file size, byte header magic number, Pillow parseability, and dimensions.
    Returns (is_valid, error_message, metadata_dict)
    """
    if len(file_bytes) == 0:
        return False, "File is empty", {}
        
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB", {}

    mime = sniff_mime_type(file_bytes)
    if mime == "unknown":
        return False, "Unsupported file format. Only JPEG and PNG images are accepted.", {}

    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify() # Verify image integrity
        
        # Re-open for dimension inspection after verify()
        image = Image.open(io.BytesIO(file_bytes))
        width, height = image.size
        
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            return False, f"Image dimensions ({width}x{height}) are below minimum required ({MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION})", {}

        metadata = {
            "mime_type": mime,
            "width": width,
            "height": height,
            "file_size": len(file_bytes),
            "format": image.format
        }
        return True, "", metadata
    except Exception as e:
        return False, f"Corrupted or invalid image file: {str(e)}", {}
