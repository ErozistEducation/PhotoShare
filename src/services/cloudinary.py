import cloudinary
import cloudinary.uploader
from src.conf.config import config

cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET
)

def upload_image(file):
    result = cloudinary.uploader.upload(file)
    return result['secure_url']

