import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import SignInRequest, SignUpRequest, TokenResponse, UserResponse
from app.dependencies import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.services.user import create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/")
def healthcheck():
    return "Server works"


@router.post("/sign-up", response_model=UserResponse)
def sign_up(user: SignUpRequest, db: Session = Depends(get_db)):
    return create_user(db, user)


@router.post("/sign-in", response_model=TokenResponse)
def sign_in(credentials: SignInRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if user is None or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id))
