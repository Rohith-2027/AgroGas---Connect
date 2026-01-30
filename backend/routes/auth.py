# backend/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import random

# import DB session & models
from database import get_db, User

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

# ==============================================
# Helper Functions
# ==============================================
def hash_password(raw: str) -> str:
    """Hash password using SHA-256 (demo only)."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_password(raw: str, hashed: str) -> bool:
    return hash_password(raw) == hashed


# ==============================================
# REGISTER USER
# ==============================================
@router.post("/register")
async def register(user: dict, db: Session = Depends(get_db)):
    """
    Register a new user.
    Expected JSON:
    {
      "name": "John",
      "role": "farmer" | "buyer" | "admin",
      "phone": "9876543210",
      "location": "Village",
      "password": "mypassword"
    }
    """
    required = ("name", "role", "phone", "password")
    for k in required:
        if k not in user or not str(user[k]).strip():
            raise HTTPException(status_code=400, detail=f"Missing field: {k}")

    phone = str(user["phone"]).strip()
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this phone already exists")

    new_user = User(
        name=str(user["name"]).strip(),
        role=str(user["role"]).strip().lower(),
        phone=phone,
        location=str(user.get("location", "")).strip(),
        password_hash=hash_password(user["password"]),
        created_at=datetime.utcnow(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "✅ User registered successfully",
        "user": {"id": new_user.id, "name": new_user.name, "role": new_user.role, "phone": new_user.phone},
    }


# ==============================================
# LOGIN USER
# ==============================================
@router.post("/login")
async def login(credentials: dict, db: Session = Depends(get_db)):
    """
    Login user.
    Expects JSON { "phone": "...", "password": "..." }
    Returns user info on success.
    """
    phone = credentials.get("phone")
    password = credentials.get("password")

    if not phone or not password:
        raise HTTPException(status_code=400, detail="phone and password required")

    user = db.query(User).filter(User.phone == str(phone).strip()).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "✅ Login successful",
        "user": {"id": user.id, "name": user.name, "role": user.role, "phone": user.phone},
    }


# ==============================================
# LIST USERS (Admin/Debug)
# ==============================================
@router.get("/users")
async def list_users(db: Session = Depends(get_db)):
    """Return all users (without password hashes)."""
    users = db.query(User).all()
    result = [
        {
            "id": u.id,
            "name": u.name,
            "role": u.role,
            "phone": u.phone,
            "location": u.location,
            "created_at": u.created_at,
        }
        for u in users
    ]
    return {"count": len(result), "users": result}


# ==============================================
# PASSWORD RESET (REQUEST)
# ==============================================
RESET_CODE_TTL_MINUTES = 15  # OTP valid for 15 minutes

@router.post("/reset-request")
async def reset_request(payload: dict, db: Session = Depends(get_db)):
    """
    Request password reset.
    Expects JSON: { "phone": "9876543210" }
    Returns: reset code (demo only — in production send via SMS/email)
    """
    phone = payload.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="phone required")

    user = db.query(User).filter(User.phone == str(phone).strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code = f"{random.randint(0,999999):06d}"
    user.reset_code = code
    user.reset_expiry = datetime.utcnow() + timedelta(minutes=RESET_CODE_TTL_MINUTES)
    db.commit()

    return {
        "message": f"Reset code valid for {RESET_CODE_TTL_MINUTES} minutes.",
        "reset_code": code,  # ⚠️ Demo only. Do not return this in real app.
    }


# ==============================================
# PASSWORD RESET (CONFIRM)
# ==============================================
@router.post("/reset-confirm")
async def reset_confirm(payload: dict, db: Session = Depends(get_db)):
    """
    Confirm password reset.
    Expects JSON:
    {
        "phone": "9876543210",
        "code": "123456",
        "new_password": "newpass"
    }
    """
    phone = payload.get("phone")
    code = payload.get("code")
    new_password = payload.get("new_password")

    if not all([phone, code, new_password]):
        raise HTTPException(status_code=400, detail="phone, code, and new_password required")

    user = db.query(User).filter(User.phone == str(phone).strip()).first()
    if not user or not user.reset_code:
        raise HTTPException(status_code=400, detail="No reset requested for this user")

    if user.reset_code != code:
        raise HTTPException(status_code=400, detail="Invalid reset code")

    if user.reset_expiry and datetime.utcnow() > user.reset_expiry:
        raise HTTPException(status_code=400, detail="Reset code expired")

    # update password and clear reset fields
    user.password_hash = hash_password(new_password)
    user.reset_code = None
    user.reset_expiry = None
    db.commit()

    return {"message": "✅ Password updated successfully"}
