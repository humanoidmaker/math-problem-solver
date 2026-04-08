import random
import string
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends

from ..core.auth import hash_password, verify_password, create_token, get_current_user
from ..core.database import get_db
from ..core.email import send_welcome_email, send_reset_email
from ..models.schemas import UserRegister, UserLogin, UserUpdate, PasswordReset, PasswordResetConfirm, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister):
    db = get_db()
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_doc = {
        "name": data.name, "email": data.email,
        "password": hash_password(data.password),
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    token = create_token(user_id, data.email)

    try:
        await send_welcome_email(data.email, data.name)
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

    return {"token": token, "user": {"id": user_id, "name": data.name, "email": data.email}}


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_id = str(user["_id"])
    token = create_token(user_id, data.email)
    return {"token": token, "user": {"id": user_id, "name": user["name"], "email": user["email"]}}


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {"id": user["_id"], "name": user["name"], "email": user["email"]}


@router.put("/me")
async def update_me(data: UserUpdate, user=Depends(get_current_user)):
    db = get_db()
    update = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
    update["updated_at"] = datetime.now(timezone.utc)
    await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": update})
    return {"message": "Profile updated"}


@router.post("/forgot-password")
async def forgot_password(data: PasswordReset):
    db = get_db()
    user = await db.users.find_one({"email": data.email})
    if not user:
        return {"message": "If the email exists, a reset code has been sent"}

    code = "".join(random.choices(string.digits, k=6))
    await db.password_resets.insert_one({
        "email": data.email, "code": code,
        "created_at": datetime.now(timezone.utc), "used": False,
    })
    try:
        await send_reset_email(data.email, user["name"], code)
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
    return {"message": "If the email exists, a reset code has been sent"}


@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    db = get_db()
    reset = await db.password_resets.find_one(
        {"email": data.email, "code": data.code, "used": False},
        sort=[("created_at", -1)],
    )
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")

    await db.password_resets.update_one({"_id": reset["_id"]}, {"$set": {"used": True}})
    await db.users.update_one(
        {"email": data.email},
        {"$set": {"password": hash_password(data.new_password), "updated_at": datetime.now(timezone.utc)}},
    )
    return {"message": "Password reset successfully"}
