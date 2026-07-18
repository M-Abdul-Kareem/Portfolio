from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import About
from ..schemas import AboutBase, AboutResponse
from ..auth import require_admin
from ..two_factor import require_2fa
from ..cloudinary_utils import upload_profile_photo

router = APIRouter(prefix="/api/about", tags=["About"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.get("", response_model=AboutResponse)
def get_about(db: Session = Depends(get_db)):
    about = db.query(About).filter(About.id == 1).first()
    if not about:
        raise HTTPException(status_code=404, detail="About content not found")
    return about


@router.put("", response_model=AboutResponse)
def update_about(payload: AboutBase, db: Session = Depends(get_db), admin: str = Depends(require_admin), _twofa: bool = Depends(require_2fa)):
    about = db.query(About).filter(About.id == 1).first()
    if not about:
        about = About(id=1)
        db.add(about)
    for field, value in payload.model_dump().items():
        setattr(about, field, value)
    db.commit()
    db.refresh(about)
    return about


@router.post("/photo", response_model=AboutResponse)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
    _twofa: bool = Depends(require_2fa),
):
    """
    Admin only — upload a profile photo to Cloudinary. Validates file
    type and size BEFORE trusting anything about it (brief's "Never
    Trust the Client" rule applies just as much to file uploads as it
    does to JSON bodies).
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: JPEG, PNG, WEBP, GIF.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        photo_url = upload_profile_photo(contents)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    about = db.query(About).filter(About.id == 1).first()
    if not about:
        about = About(id=1)
        db.add(about)

    # Cloudinary uses a fixed public_id (overwrite=True), so old
    # versions are automatically replaced — no orphaned files to clean
    # up locally, unlike the old disk-based approach.
    about.photo_url = photo_url
    db.commit()
    db.refresh(about)
    return about
