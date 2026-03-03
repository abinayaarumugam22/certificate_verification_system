import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token
from app.models.certificate import User, Institution, UserRole
from app.schemas.certificate import UserRegister, UserLogin, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register_user(data: UserRegister, db: Session = Depends(get_db)):
    """Register institution / student / verifier"""

    # Check email exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate role
    valid_roles = ["institution", "student", "verifier"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of {valid_roles}")

    institution_id = None

    # If institution role → create institution record
    if data.role == "institution":
        inst = Institution(
            id      = str(uuid.uuid4()),
            name    = data.full_name,
            code    = data.institution_code or str(uuid.uuid4())[:8].upper(),
            address = ""
        )
        db.add(inst)
        db.flush()
        institution_id = inst.id

    # If student → find institution by code
    if data.role == "student" and data.institution_code:
        inst = db.query(Institution).filter(
            Institution.code == data.institution_code
        ).first()
        if inst:
            institution_id = inst.id

    # Create user
    user = User(
        id              = str(uuid.uuid4()),
        full_name       = data.full_name,
        email           = data.email,
        hashed_password = hash_password(data.password),
        role            = UserRole(data.role),
        institution_id  = institution_id,
        register_number = data.register_number
    )
    db.add(user)
    db.commit()

    return {
        "message":  f"✅ {data.role.capitalize()} registered successfully",
        "email":    data.email,
        "role":     data.role
    }


@router.post("/login", response_model=TokenResponse)
def login_user(data: UserLogin, db: Session = Depends(get_db)):
    """Login and get JWT token"""

    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "sub":  user.id,
        "role": user.role.value,
        "name": user.full_name
    })

    return TokenResponse(
        access_token = token,
        token_type   = "bearer",
        role         = user.role.value,
        full_name    = user.full_name
    )