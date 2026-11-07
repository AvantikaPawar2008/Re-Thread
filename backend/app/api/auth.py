"""Account endpoints used by the frontend: register, login, and profile."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models_db import User

router = APIRouter(prefix="/auth", tags=["Accounts"])

# Set RETHREAD_SECRET in your environment before deploying.
SECRET = os.environ.get("RETHREAD_SECRET", "dev-only-change-me").encode()
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days
PBKDF2_ITERATIONS = 200_000


# ---------- helpers ----------

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def make_token(user_id: int) -> str:
    payload = json.dumps({"uid": user_id, "exp": int(time.time()) + TOKEN_TTL_SECONDS}).encode()
    signature = hmac.new(SECRET, payload, hashlib.sha256).digest()
    return f"{_b64(payload)}.{_b64(signature)}"


def read_token(token: str) -> Optional[int]:
    try:
        payload_part, signature_part = token.split(".")
        payload = _unb64(payload_part)
        expected = hmac.new(SECRET, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(_unb64(signature_part), expected):
            return None
        data = json.loads(payload)
        if data["exp"] < time.time():
            return None
        return int(data["uid"])
    except Exception:
        return None


def to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "city": user.city or "",
        "bio": user.bio or "",
        "interests": user.interests or "",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in again.")
    user_id = read_token(authorization[len("Bearer "):])
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in again.")
    return user


# ---------- schemas ----------

class RegisterIn(BaseModel):
    full_name: str
    email: str
    password: str
    city: Optional[str] = "Pune"


class LoginIn(BaseModel):
    email: str
    password: str


class ProfilePatch(BaseModel):
    full_name: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[str] = None


def _bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


# ---------- routes ----------

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    name = body.full_name.strip()
    email = body.email.strip().lower()
    city = (body.city or "Pune").strip() or "Pune"

    if len(name) < 2:
        raise _bad_request("Please enter your name.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise _bad_request("Enter a valid email address.")
    if len(body.password) < 8:
        raise _bad_request("Use at least 8 characters.")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        full_name=name[:120],
        email=email,
        password_hash=hash_password(body.password),
        city=city[:80],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": make_token(user.id), "user": to_dict(user)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    return {"token": make_token(user.id), "user": to_dict(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return to_dict(user)


@router.put("/me")
def update_me(
    patch: ProfilePatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = patch.model_dump(exclude_none=True)
    if "full_name" in data:
        if len(data["full_name"].strip()) < 2:
            raise _bad_request("Please enter your name.")
        user.full_name = data["full_name"].strip()[:120]
    if "city" in data:
        user.city = data["city"].strip()[:80]
    if "bio" in data:
        user.bio = data["bio"][:500]
    if "interests" in data:
        user.interests = data["interests"][:255]
    db.commit()
    db.refresh(user)
    return to_dict(user)