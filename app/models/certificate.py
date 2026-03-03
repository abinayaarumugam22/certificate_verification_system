import enum
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from app.core.database import Base


class UserRole(str, enum.Enum):
    admin       = "admin"
    institution = "institution"
    student     = "student"
    verifier    = "verifier"


class Institution(Base):
    __tablename__ = "institutions"

    id         = Column(String, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)
    code       = Column(String(100), unique=True, nullable=False)
    address    = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id              = Column(String, primary_key=True, index=True)
    full_name       = Column(String(255), nullable=False)
    email           = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(Enum(UserRole), nullable=False)
    institution_id  = Column(String, ForeignKey("institutions.id"), nullable=True)
    register_number = Column(String(100), nullable=True)
    is_active       = Column(String(10), default="true")
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class Certificate(Base):
    __tablename__   = "certificates"

    certificate_id      = Column(String, primary_key=True, index=True)
    student_name        = Column(String(255), nullable=False)
    register_number     = Column(String(100), nullable=False, unique=True, index=True)
    issue_date          = Column(String(50),  nullable=False)
    sha256_hash         = Column(String(64),  nullable=False)
    phash               = Column(String(64),  nullable=False)
    original_image_path = Column(String(500), nullable=False)
    institution_id      = Column(String, ForeignKey("institutions.id"), nullable=True)
    uploaded_by         = Column(String, ForeignKey("users.id"),         nullable=True)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id             = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    certificate_id = Column(String, ForeignKey("certificates.certificate_id"), nullable=True)
    verified_by    = Column(String, ForeignKey("users.id"),                    nullable=True)
    status         = Column(String(50),  nullable=False)
    ssim_score     = Column(String(20),  nullable=True)
    phash_distance = Column(String(10),  nullable=True)
    tampered_image = Column(String(500), nullable=True)
    verified_at    = Column(DateTime(timezone=True), server_default=func.now())