"""Bounded local security checks for untrusted uploaded documents."""
from pathlib import Path

import pymupdf
from PIL import Image, UnidentifiedImageError


SCANNER_VERSION = 'aegis-upload-scan-1'
EICAR_MARKER = b''.join((b'X5O!P%@AP[4', b'\\PZX54(P^)7CC)7}$', b'EICAR-STANDARD-ANTIVIRUS-', b'TEST-FILE!$H+H*'))
EXECUTABLE_MAGIC = (b'MZ', b'\x7fELF')
PDF_BLOCKED_MARKERS = {
    b'/JavaScript': 'embedded JavaScript',
    b'/JS': 'embedded JavaScript action',
    b'/Launch': 'launch action',
    b'/EmbeddedFile': 'embedded file',
    b'/RichMedia': 'rich media content',
}


class UnsafeUpload(ValueError):
    pass


def scan_upload(path, suffix):
    """Return a clean scan record or raise UnsafeUpload before persistence."""
    path = Path(path)
    content = path.read_bytes()
    if EICAR_MARKER in content:
        raise UnsafeUpload('Upload blocked: antivirus test or malware signature detected.')
    if content.startswith(EXECUTABLE_MAGIC):
        raise UnsafeUpload('Upload blocked: executable content is not accepted as a document.')

    findings = []
    suffix = suffix.lower()
    if suffix == '.pdf':
        for marker, label in PDF_BLOCKED_MARKERS.items():
            if marker in content:
                raise UnsafeUpload(f'Upload blocked: PDF contains {label}.')
        try:
            with pymupdf.open(path) as pdf:
                if pdf.needs_pass:
                    raise UnsafeUpload('Upload blocked: password-protected PDFs cannot be safely inspected.')
                if len(pdf) > 100:
                    raise UnsafeUpload('Upload blocked: PDF exceeds the 100-page inspection limit.')
                for page in pdf:
                    if len(page.get_links()) > 100:
                        raise UnsafeUpload('Upload blocked: PDF contains an excessive number of links.')
        except UnsafeUpload:
            raise
        except Exception as exc:
            raise UnsafeUpload('Upload blocked: PDF structure could not be safely inspected.') from exc
    elif suffix in {'.png', '.jpg', '.jpeg'}:
        try:
            with Image.open(path) as image:
                width, height = image.size
                if width * height > 25_000_000:
                    raise UnsafeUpload('Upload blocked: image exceeds the safe pixel limit.')
                image.verify()
        except UnsafeUpload:
            raise
        except (UnidentifiedImageError, OSError) as exc:
            raise UnsafeUpload('Upload blocked: image structure could not be safely inspected.') from exc
    elif suffix in {'.txt', '.csv'}:
        if content.count(b'\x00'):
            raise UnsafeUpload('Upload blocked: binary content was found in a text document.')

    return {'status': 'clean', 'findings': findings, 'scanner_version': SCANNER_VERSION}
