# books_api/cloudinary_helper.py
import cloudinary
import cloudinary.uploader
from django.conf import settings

# Konfiguro Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)


def upload_to_cloudinary(file, folder, resource_type='auto'):
    """Upload file to Cloudinary dhe kthe URL"""
    try:
        # Upload file
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type=resource_type,
            unique_filename=True,
            overwrite=False
        )

        # Kthe secure URL
        return {
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'format': result.get('format', ''),
            'width': result.get('width', 0),
            'height': result.get('height', 0),
            'size': result.get('bytes', 0)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Në cloudinary_helper.py
def get_optimized_image_url(public_id, width=300, height=400):
    """Gjeneron URL për version të optimizuar"""
    from cloudinary import CloudinaryImage

    return CloudinaryImage(public_id).build_url(
        width=width,
        height=height,
        crop="fill",
        quality="auto",
        fetch_format="auto"
    )


# Në model ose serializer
def get_thumbnail_url(self):
    if self.cover_public_id:
        return get_optimized_image_url(self.cover_public_id, 150, 200)
    return ''