from pydantic import BaseModel
from typing import Optional

# ─── INPUT SCHEMAS (Request) ───────────────────────────

class CertificateCreate(BaseModel):
    """Schema for creating/registering a new certificate"""
    student_name:    str
    register_number: str
    issue_date:      str

class BulkCertificateItem(BaseModel):
    """Single item in bulk upload"""
    student_name:    str
    register_number: str
    issue_date:      str

# ─── OUTPUT SCHEMAS (Response) ─────────────────────────

class CertificateResponse(BaseModel):
    certificate_id:      str
    student_name:        str
    register_number:     str
    issue_date:          str
    sha256_hash:         str
    phash:               str
    original_image_path: str
    message:             str

    class Config:
        from_attributes = True

class VerificationResponse(BaseModel):
    """Response after verifying a certificate"""
    status:           str            # VALID / POSSIBLY_VALID / INVALID
    certificate_id:   Optional[str]
    student_name:     Optional[str]
    register_number:  Optional[str]
    issue_date:       Optional[str]
    sha256_match:     bool
    phash_distance:   Optional[int]
    ssim_score:       Optional[float]
    tampered_image:   Optional[str]  # path to highlighted image
    message:          str
from pydantic import BaseModel, EmailStr
from typing import Optional

# ── AUTH SCHEMAS ────────────────────────────────────

class UserRegister(BaseModel):
    full_name:       str
    email:           str
    password:        str
    role:            str   # institution / student / verifier
    register_number: Optional[str] = None   # required if role=student
    institution_code: Optional[str] = None  # required if role=institution/student

class UserLogin(BaseModel):
    email:    str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str
    role:         str
    full_name:    str

# ── CERTIFICATE SCHEMAS ─────────────────────────────

class CertificateCreate(BaseModel):
    student_name:    str
    register_number: str
    issue_date:      str

class CertificateResponse(BaseModel):
    certificate_id:      str
    student_name:        str
    register_number:     str
    issue_date:          str
    sha256_hash:         str
    phash:               str
    original_image_path: str
    message:             str

    class Config:
        from_attributes = True

class VerificationResponse(BaseModel):
    status:          str
    certificate_id:  Optional[str]
    student_name:    Optional[str]
    register_number: Optional[str]
    issue_date:      Optional[str]
    sha256_match:    bool
    phash_distance:  Optional[int]
    ssim_score:      Optional[float]
    tampered_image:  Optional[str]
    message:         str