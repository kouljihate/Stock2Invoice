"""Helpers for user-uploaded images.

Kept in one place so the company logo is validated and stored identically
whether it arrives from the first-login setup wizard or the admin panel.
"""

import os
from uuid import uuid4

from flask import current_app

ALLOWED_IMAGE_EXTENSIONS = frozenset({'png', 'jpg', 'jpeg', 'gif', 'webp'})
MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4 MB


class UploadError(ValueError):
    """Raised when an uploaded file is not an acceptable image."""


def save_logo(file, subdir='logos'):
    """Store an uploaded logo and return its generated file name.

    Returns ``None`` when no file was submitted, so callers can treat the
    logo as optional. Raises :class:`UploadError` for a wrong type or an
    oversized file, which callers turn into a form error.
    """
    if file is None or not getattr(file, 'filename', ''):
        return None

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise UploadError('Logo must be a PNG, JPG, GIF or WEBP image.')

    stream = file.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if size > MAX_IMAGE_BYTES:
        raise UploadError('Logo must be smaller than 4 MB.')

    filename = '%s.%s' % (uuid4().hex, ext)
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', subdir)
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return filename
