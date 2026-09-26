from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import SignUpRequest
from app.core.security import hash_password


def create_user(db: Session, user: SignUpRequest):
    # if user.password != user.confirm_password:
    #     return {"message": "Password not match"}
    db_user = User(
        username=user.username, email=user.email, password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
