import os
import shutil
import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.certificate import CertificateCreate, CertificateResponse
from app.services.certificate_service import register_certificate
from app.core.config import settings
import zipfile

router = APIRouter(prefix="/admin", tags=["Admin"])


def save_uploaded_file(upload_file: UploadFile, destination: str) -> str:
    """Save uploaded file to destination path"""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return destination


# ─────────────────────────────────────────
# SINGLE CERTIFICATE UPLOAD
# ─────────────────────────────────────────
@router.post("/register", response_model=CertificateResponse)
async def register_single_certificate(
    student_name:    str        = Form(...),
    register_number: str        = Form(...),
    issue_date:      str        = Form(...),
    file:            UploadFile = File(...),
    db:              Session    = Depends(get_db)
):
    """
    Register a single certificate.
    - Upload image or PDF
    - Enter student details
    - System generates QR, embeds it, stores hashes
    """

    # Validate file type
    allowed = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, PDF files are allowed"
        )

    # Save uploaded file temporarily
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{file.filename}")
    save_uploaded_file(file, temp_path)

    # Handle PDF → convert to image
    if file.content_type == "application/pdf":
        from pdf2image import convert_from_path
        pages = convert_from_path(temp_path, dpi=200)
        image_path = temp_path.replace(".pdf", ".jpg")
        pages[0].save(image_path, "JPEG")
        os.remove(temp_path)
    else:
        image_path = temp_path

    # Register certificate
    data = CertificateCreate(
        student_name    = student_name,
        register_number = register_number,
        issue_date      = issue_date
    )
    try:
        result = register_certificate(
            db             = db,
            data           = data,
            image_path     = image_path,
            uploaded_by    = None,
            institution_id = None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    return result


# ─────────────────────────────────────────
# BULK UPLOAD (Excel/CSV)
# ─────────────────────────────────────────


@router.post("/bulk-register")
async def bulk_register_certificates(
    excel_file: UploadFile = File(..., description="Excel/CSV with student details"),
    zip_file:   UploadFile = File(..., description="ZIP file containing all certificate images"),
    db:         Session    = Depends(get_db)
):
    """
    Bulk register certificates.
    Excel columns: student_name, register_number, issue_date, certificate_file
    ZIP file: contains all certificate images mentioned in Excel
    """

    # ── Step 1: Save Excel ──────────────────────────
    excel_path = os.path.join(settings.UPLOAD_DIR, f"bulk_{excel_file.filename}")
    save_uploaded_file(excel_file, excel_path)

    # ── Step 2: Read Excel/CSV ──────────────────────
    try:
        if excel_file.filename.endswith(".csv"):
            df = pd.read_csv(excel_path)
        else:
            df = pd.read_excel(excel_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read Excel: {str(e)}")

    # ── Step 3: Validate columns ────────────────────
    required_cols = ["student_name", "register_number", "issue_date", "certificate_file"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns in Excel: {missing}"
        )

    # ── Step 4: Save and Extract ZIP ────────────────
    zip_path = os.path.join(settings.UPLOAD_DIR, f"bulk_{zip_file.filename}")
    save_uploaded_file(zip_file, zip_path)

    # Extract ZIP to a temp folder
    extract_folder = os.path.join(settings.UPLOAD_DIR, "bulk_extracted")
    os.makedirs(extract_folder, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_folder)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")

    # ── Step 5: Process each row ────────────────────
    results = []
    errors  = []

    for index, row in df.iterrows():
        try:
            student_name    = str(row["student_name"]).strip()
            register_number = str(row["register_number"]).strip()
            issue_date      = str(row["issue_date"]).strip()
            cert_filename   = str(row["certificate_file"]).strip()

            # Find image in extracted folder
            image_path = _find_image_in_folder(extract_folder, cert_filename)

            if image_path is None:
                errors.append({
                    "row":            index + 1,
                    "student_name":   student_name,
                    "certificate_file": cert_filename,
                    "error":          f"Image '{cert_filename}' not found in ZIP"
                })
                continue

            # Handle PDF inside ZIP
            if cert_filename.lower().endswith(".pdf"):
                from pdf2image import convert_from_path
                pages = convert_from_path(image_path, dpi=200)
                converted_path = image_path.replace(".pdf", ".jpg")
                pages[0].save(converted_path, "JPEG")
                image_path = converted_path

            # Register certificate
            data = CertificateCreate(
                student_name    = student_name,
                register_number = register_number,
                issue_date      = issue_date
            )

            result = register_certificate(db, data, image_path)

            results.append({
                "row":              index + 1,
                "student_name":     student_name,
                "register_number":  register_number,
                "certificate_id":   result.certificate_id,
                "status":           "✅ success"
            })

        except Exception as e:
            errors.append({
                "row":          index + 1,
                "student_name": str(row.get("student_name", "unknown")),
                "error":        str(e)
            })

    # ── Step 6: Cleanup extracted folder ────────────
    import shutil
    shutil.rmtree(extract_folder, ignore_errors=True)
    os.remove(zip_path)

    return {
        "total":   len(df),
        "success": len(results),
        "failed":  len(errors),
        "results": results,
        "errors":  errors
    }


def _find_image_in_folder(folder: str, filename: str) -> str | None:
    """
    Search for image file inside extracted ZIP folder.
    Handles nested subfolders too.
    """
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower() == filename.lower():
                return os.path.join(root, f)
    return None

def _get_or_create_template() -> str:
    """Create a blank white template image if none exists"""
    from PIL import Image
    template_path = os.path.join(settings.UPLOAD_DIR, "bulk_template.jpg")
    if not os.path.exists(template_path):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(template_path)
    return template_path


# ─────────────────────────────────────────
# GET CERTIFICATE BY ID
# ─────────────────────────────────────────
@router.get("/certificate/{certificate_id}")
def get_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """Fetch certificate details by ID"""
    from app.models.certificate import Certificate
    cert = db.query(Certificate).filter(
        Certificate.certificate_id == certificate_id
    ).first()

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    return {
        "certificate_id":      cert.certificate_id,
        "student_name":        cert.student_name,
        "register_number":     cert.register_number,
        "issue_date":          cert.issue_date,
        "original_image_path": cert.original_image_path,
        "qr_image_path":       cert.qr_image_path,
        "created_at":          cert.created_at
    }


# ─────────────────────────────────────────
# LIST ALL CERTIFICATES
# ─────────────────────────────────────────
@router.get("/certificates")
def list_certificates(
    skip:  int     = 0,
    limit: int     = 20,
    db:    Session = Depends(get_db)
):
    """List all registered certificates with pagination"""
    from app.models.certificate import Certificate
    certs = db.query(Certificate).offset(skip).limit(limit).all()
    total = db.query(Certificate).count()

    return {
        "total": total,
        "skip":  skip,
        "limit": limit,
        "data": [
            {
                "certificate_id":  c.certificate_id,
                "student_name":    c.student_name,
                "register_number": c.register_number,
                "issue_date":      c.issue_date,
                "created_at":      c.created_at
            }
            for c in certs
        ]
    }