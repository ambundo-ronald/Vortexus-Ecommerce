def delete_product_image_with_file(image) -> str:
    original = getattr(image, 'original', None)
    filename = getattr(original, 'name', '') or ''
    storage = getattr(original, 'storage', None)

    if filename and storage and storage.exists(filename):
        storage.delete(filename)

    image.delete()
    return filename
