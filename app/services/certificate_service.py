import os
import uuid
import shutil
from sqlalchemy.orm import Session
from app.models.certificate import Certificate
from app.schemas.certificate import CertificateCreate, CertificateResponse, VerificationResponse
from app.utils.hash_utils import generate_sha256, generate_phash, hamming_distance
from app.utils.tamper_detection import highlight_tampered_regions
from app.core.config import settings


PHASH_THRESHOLD_VALID = 5   # only informational
SSIM_THRESHOLD = 0.998      # strong similarity required


# ===============================
# REGISTER CERTIFICATE
# ===============================
def register_certificate(
    db: Session,
    data: CertificateCreate,
    image_path: str,
    uploaded_by: str = None,
    institution_id: str = None
) -> CertificateResponse:

    existing = db.query(Certificate).filter(
        Certificate.register_number == data.register_number
    ).first()

    if existing:
        raise ValueError(f"Register number {data.register_number} already registered")

    certificate_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"

    # Save permanent original image
    original_filename = f"{certificate_id}_original.jpg"
    permanent_path = os.path.join(settings.UPLOAD_DIR, original_filename)

    shutil.copy(image_path, permanent_path)

    sha256 = generate_sha256(permanent_path)
    phash = generate_phash(permanent_path)

    cert = Certificate(
        certificate_id=certificate_id,
        student_name=data.student_name,
        register_number=data.register_number,
        issue_date=data.issue_date,
        sha256_hash=sha256,
        phash=phash,
        original_image_path=permanent_path,
        institution_id=institution_id,
        uploaded_by=uploaded_by
    )

    db.add(cert)
    db.commit()
    db.refresh(cert)

    return CertificateResponse(
        certificate_id=cert.certificate_id,
        student_name=cert.student_name,
        register_number=cert.register_number,
        issue_date=cert.issue_date,
        sha256_hash=cert.sha256_hash,
        phash=cert.phash,
        original_image_path=cert.original_image_path,
        message="✅ Certificate registered successfully"
    )


# ===============================
# VERIFY CERTIFICATE
# ===============================
def verify_certificate(
    db: Session,
    uploaded_path: str,
    register_number: str
) -> VerificationResponse:

    # Step 1: Find certificate
    cert = db.query(Certificate).filter(
        Certificate.register_number == register_number
    ).first()

    if not cert:
        return VerificationResponse(
            status="INVALID",
            certificate_id=None,
            student_name=None,
            register_number=register_number,
            issue_date=None,
            sha256_match=False,
            phash_distance=None,
            ssim_score=None,
            tampered_image=None,
            message=f"❌ No certificate found for register number: {register_number}"
        )

    # Step 2: Generate uploaded hashes
    uploaded_sha256 = generate_sha256(uploaded_path)
    uploaded_phash = generate_phash(uploaded_path)

    # Step 3: Exact SHA256 match
    if uploaded_sha256 == cert.sha256_hash:
        return VerificationResponse(
            status="VALID",
            certificate_id=cert.certificate_id,
            student_name=cert.student_name,
            register_number=cert.register_number,
            issue_date=cert.issue_date,
            sha256_match=True,
            phash_distance=0,
            ssim_score=1.0,
            tampered_image=None,
            message="✅ Certificate is VALID (exact match)"
        )

    # Step 4: pHash comparison (INFO ONLY — no early return)
    distance = hamming_distance(uploaded_phash, cert.phash)

    # Step 5: ALWAYS run SSIM
    tampered_output = os.path.join(
        settings.UPLOAD_DIR,
        f"{cert.certificate_id}_tampered.jpg"
    )

    ssim_score, tampered_path = highlight_tampered_regions(
        original_path=cert.original_image_path,
        uploaded_path=uploaded_path,
        output_path=tampered_output
    )

    # Step 6: Final Decision (based ONLY on SSIM)
    if ssim_score >= SSIM_THRESHOLD:
        status = "VALID"
        message = f"✅ Certificate is VALID (SSIM: {ssim_score:.4f})"
        tampered_path = None
    else:
        status = "TAMPERED"
        message = f"❌ Certificate is TAMPERED (SSIM: {ssim_score:.4f})"

    return VerificationResponse(
        status=status,
        certificate_id=cert.certificate_id,
        student_name=cert.student_name,
        register_number=cert.register_number,
        issue_date=cert.issue_date,
        sha256_match=False,
        phash_distance=distance,
        ssim_score=round(ssim_score, 4),
        tampered_image=tampered_path,
        message=message
    )