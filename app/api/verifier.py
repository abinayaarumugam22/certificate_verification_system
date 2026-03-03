import os
import shutil
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.certificate import VerificationResponse
from app.services.certificate_service import verify_certificate
from app.core.config import settings

router = APIRouter(prefix="/verify", tags=["Verifier"])


@router.post("/", response_model=VerificationResponse)
async def verify_uploaded_certificate(
    register_number: str        = Form(...),
    file:            UploadFile = File(...),
    db:              Session    = Depends(get_db)
):
    # Validate file type
    allowed = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, PDF allowed")

    # Save uploaded file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    img_path = os.path.join(settings.UPLOAD_DIR, f"verify_{file.filename}")

    with open(img_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Handle PDF
    if file.content_type == "application/pdf":
        from pdf2image import convert_from_path
        pages    = convert_from_path(img_path, dpi=200)
        jpg_path = img_path.replace(".pdf", ".jpg")
        pages[0].save(jpg_path, "JPEG")
        os.remove(img_path)
        img_path = jpg_path

    # Run verification
    try:
        result = verify_certificate(db, img_path, register_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result


@router.get("/tampered-image/{filename}")
def get_tampered_image(filename: str):
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path, media_type="image/jpeg")


@router.post("/read-existing-qr")
async def read_existing_qr(file: UploadFile = File(...)):
    """Debug endpoint - read QR from certificate"""
    import cv2
    temp_path = os.path.join(settings.UPLOAD_DIR, f"qrread_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img      = cv2.imread(temp_path)
    detector = cv2.QRCodeDetector()
    raw_data, bbox, _ = detector.detectAndDecode(img)

    return {
        "qr_detected":    bool(raw_data),
        "raw_qr_content": raw_data if raw_data else "Not detected"
    }