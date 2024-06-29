import enum
from datetime import date,datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    Enum,
    Boolean,
    func,
    Table,
    Column,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Todo(Base):
    __tablename__ = "todos"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(String(250))
    completed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[date] = mapped_column(
        DateTime, default=func.now(), nullable=True
    )
    updated_at: Mapped[date] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship("User", back_populates="todos", lazy="joined")


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[date] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role), default=Role.user, nullable=True
    )
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    todos: Mapped["Todo"] = relationship("Todo", back_populates="user", lazy="joined")
    photos: Mapped["Photo"] = relationship("Photo", back_populates="user", lazy="joined")
    comments: Mapped["Comment"] = relationship("Comment", back_populates="user", lazy="joined")


class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[date] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="photos", lazy="joined")
    tags: Mapped["Tag"] = relationship("Tag", secondary="photo_tags", back_populates="photos")
    comments: Mapped["Comment"] = relationship("Comment", back_populates="photo", lazy="joined")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    photos: Mapped["Photo"] = relationship(
        "Photo", secondary="photo_tags", back_populates="tags"
    )


photo_tags = Table(
    "photo_tags",
    Base.metadata,
    Column("photo_id", ForeignKey("photos.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[date] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="comments", lazy="joined")
    photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id"))
    photo: Mapped["Photo"] = relationship("Photo", back_populates="comments", lazy="joined")

