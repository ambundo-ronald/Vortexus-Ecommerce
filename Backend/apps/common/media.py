from __future__ import annotations

from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, UnidentifiedImageError


def allowed_image_extensions() -> set[str]:
    return {str(ext).lower() for ext in getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.webp'])}


def validate_uploaded_image(file_obj, *, max_bytes: int | None = None) -> None:
    max_bytes = max_bytes or int(getattr(settings, 'MAX_IMAGE_UPLOAD_BYTES', 5 * 1024 * 1024))
    extension = Path(getattr(file_obj, 'name', '') or '').suffix.lower()
    if extension not in allowed_image_extensions():
        raise ValueError(f'Unsupported image file type: {extension or "unknown"}')

    file_size = getattr(file_obj, 'size', None)
    if file_size and file_size > max_bytes:
        raise ValueError(f'Image exceeds the maximum allowed size of {max_bytes} bytes.')

    current_position = None
    if hasattr(file_obj, 'tell'):
        current_position = file_obj.tell()
    try:
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
        image = Image.open(file_obj)
        image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError('Uploaded file is not a valid image.') from exc
    finally:
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0 if current_position is None else current_position)


def validate_local_image_path(path: Path, *, max_bytes: int | None = None) -> None:
    max_bytes = max_bytes or int(getattr(settings, 'MAX_PRODUCT_IMAGE_BYTES', 10 * 1024 * 1024))
    extension = path.suffix.lower()
    if extension not in allowed_image_extensions():
        raise ValueError(f'Unsupported image file type: {extension or "unknown"}')
    if path.stat().st_size > max_bytes:
        raise ValueError(f'Image exceeds the maximum allowed size of {max_bytes} bytes.')
    try:
        with path.open('rb') as handle:
            image = Image.open(handle)
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f'File is not a valid image: {path}') from exc


def normalize_uploaded_image(
    file_obj,
    *,
    max_bytes: int | None = None,
    max_dimension: int | None = None,
):
    max_bytes = max_bytes or int(getattr(settings, 'MAX_IMAGE_UPLOAD_BYTES', 5 * 1024 * 1024))
    max_dimension = max_dimension or int(getattr(settings, 'MAX_IMAGE_DIMENSION', 1600))
    target_format = str(getattr(settings, 'NORMALIZED_IMAGE_FORMAT', 'WEBP')).upper()
    quality = int(getattr(settings, 'NORMALIZED_IMAGE_QUALITY', 82))

    validate_uploaded_image(file_obj, max_bytes=max_bytes * 4)

    original_name = getattr(file_obj, 'name', 'upload')
    file_size = getattr(file_obj, 'size', None) or 0

    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)
    image = Image.open(file_obj)
    image.load()
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)

    needs_resize = max(image.size) > max_dimension
    needs_reencode = file_size > max_bytes or Path(original_name).suffix.lower() not in allowed_image_extensions()
    if not needs_resize and not needs_reencode:
        return file_obj

    content, extension, content_type = _normalized_image_content(
        image=image,
        max_bytes=max_bytes,
        max_dimension=max_dimension,
        target_format=target_format,
        quality=quality,
    )
    normalized_name = f'{Path(original_name).stem or "image"}{extension}'
    return SimpleUploadedFile(normalized_name, content, content_type=content_type)


def normalize_local_image_bytes(path: Path, *, max_bytes: int | None = None, max_dimension: int | None = None):
    max_bytes = max_bytes or int(getattr(settings, 'MAX_PRODUCT_IMAGE_BYTES', 10 * 1024 * 1024))
    max_dimension = max_dimension or int(getattr(settings, 'MAX_PRODUCT_IMAGE_DIMENSION', 2400))
    target_format = str(getattr(settings, 'NORMALIZED_IMAGE_FORMAT', 'WEBP')).upper()
    quality = int(getattr(settings, 'NORMALIZED_IMAGE_QUALITY', 82))

    validate_local_image_path(path, max_bytes=max_bytes * 4)

    with path.open('rb') as handle:
        image = Image.open(handle)
        image.load()

    if path.stat().st_size <= max_bytes and max(image.size) <= max_dimension:
        return path.name, path.read_bytes()

    content, extension, _ = _normalized_image_content(
        image=image,
        max_bytes=max_bytes,
        max_dimension=max_dimension,
        target_format=target_format,
        quality=quality,
    )
    normalized_name = f'{path.stem}{extension}'
    return normalized_name, content


def _normalized_image_content(*, image: Image.Image, max_bytes: int, max_dimension: int, target_format: str, quality: int):
    working = image.copy()
    if working.mode not in ('RGB', 'RGBA'):
        working = working.convert('RGBA' if 'A' in working.getbands() else 'RGB')
    if max(working.size) > max_dimension:
        working.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    attempt_quality = quality
    last_content = b''
    while attempt_quality >= 45:
        buffer = BytesIO()
        save_image = working
        save_kwargs = {'format': target_format, 'optimize': True}
        if target_format in {'JPEG', 'WEBP'}:
            if target_format == 'JPEG' and save_image.mode != 'RGB':
                background = Image.new('RGB', save_image.size, (255, 255, 255))
                if save_image.mode != 'RGBA':
                    save_image = save_image.convert('RGBA')
                background.paste(save_image, mask=save_image.split()[-1])
                save_image = background
            save_kwargs['quality'] = attempt_quality
        save_image.save(buffer, **save_kwargs)
        last_content = buffer.getvalue()
        if len(last_content) <= max_bytes:
            break
        attempt_quality -= 7

    extension_map = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}
    content_type_map = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}
    return (
        last_content,
        extension_map.get(target_format, '.img'),
        content_type_map.get(target_format, 'application/octet-stream'),
    )
