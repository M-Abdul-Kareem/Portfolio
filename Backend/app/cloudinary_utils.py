"""
Cloudinary integration — replaces local disk storage for uploaded photos.

Why: serverless hosting (Vercel) has no persistent local filesystem —
anything written to disk during one request is gone by the next, since
each invocation may run in a fresh container. Cloudinary stores the
actual image file permanently and gives back a stable URL, which is
what gets saved in the database instead of a local file path.

Configuration: reads credentials from environment variables, all three
of which come from your Cloudinary account dashboard:
    CLOUDINARY_CLOUD_NAME
    CLOUDINARY_API_KEY
    CLOUDINARY_API_SECRET
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.exceptions

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure=True,
)

# A fixed public_id means every new photo upload OVERWRITES the same
# Cloudinary asset instead of accumulating unlimited orphaned images —
# important given the free tier's limited monthly credits.
PROFILE_PHOTO_PUBLIC_ID = "portfolio/profile_photo"


def is_configured() -> bool:
    """True if Cloudinary credentials are actually set."""
    cfg = cloudinary.config()
    return bool(cfg.cloud_name and cfg.api_key and cfg.api_secret)


def upload_profile_photo(file_bytes: bytes) -> str:
    """
    Uploads (or overwrites) the profile photo on Cloudinary and returns
    its public HTTPS URL. Raises RuntimeError with a clear message if
    Cloudinary isn't configured or the upload fails, so the caller can
    turn that into a proper HTTP error response.
    """
    if not is_configured():
        raise RuntimeError(
            "Cloudinary is not configured. Set CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET as environment variables."
        )

    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            public_id=PROFILE_PHOTO_PUBLIC_ID,
            overwrite=True,
            invalidate=True,  # bust any CDN cache of the old photo
            folder=None,      # public_id already includes the "portfolio/" prefix
            resource_type="image",
        )
        return result["secure_url"]
    except cloudinary.exceptions.Error as e:
        raise RuntimeError(f"Cloudinary upload failed: {e}")
