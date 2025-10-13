from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from service.users_service import create_user, get_user_by_username, get_user_by_email
from auth import hash_password, verify_password, create_access_token
from datetime import timedelta
from models.auth_models import SignUpRequest
 
router = APIRouter(prefix="/auth", tags=["Auth"])
 
@router.post("/signup")
def signup(request: SignUpRequest):
    existing = get_user_by_username(request.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
 
    password_hash = hash_password(request.password)
    success = create_user(request.username, request.email, password_hash, request.role)
    if not success:
        raise HTTPException(status_code=500, detail="User creation failed")
 
    return {"message": "✅ User created successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(form_data.username)  # use 'username' as email here
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    role = user[4]

    if not verify_password(form_data.password, user[3]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=30)
    token = create_access_token(data={"sub": user[2]}, expires_delta=access_token_expires)  # user[2] for email

    user_data = {
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "role": role
    }
    return {"user": user_data, "token": token}

 