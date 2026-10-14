from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.strip().lower()).first()

    def list_users(self, role: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None) -> List[User]:
        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        if status:
            query = query.filter(User.status == status)
        if search:
            s = f"%{search}%"
            query = query.filter((User.name.ilike(s)) | (User.email.ilike(s)))
        return query.order_by(User.id.asc()).all()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user
