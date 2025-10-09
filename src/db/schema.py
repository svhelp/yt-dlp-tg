import enum
from typing import List
from typing import Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class RequestStatus(enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    
class RequestType(enum.Enum):
    INLINE = "inline"
    PERSONAL = "personal"
    CATCHED = "catched"
        
class UserTier(enum.Enum):
    LIMITED = "limited"
    REGULAR = "regular"
    ADVANCED = "advanced"

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    username: Mapped[str] = mapped_column(String(30))
    tier: Mapped[UserTier] = mapped_column(
        Enum(UserTier, native_enum=False),
        default=UserTier.REGULAR,
        nullable=False
    )
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    requests: Mapped[List["Request"]] = relationship(
        back_populates="user_account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, username={self.username!r}, tier={self.tier!r}, is_banned={self.is_banned!r})"
    
class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(255))

    video: Mapped["Video"] = relationship(back_populates="file", uselist=False)

    def __repr__(self) -> str:
        return f"File(id={self.id!r}, path={self.path!r})"
    
class VideoAuthor(Base):
    __tablename__ = "video_author"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(30))

    videos: Mapped[List["Video"]] = relationship(back_populates="author")

    def __repr__(self) -> str:
        return f"VideoAuthor(id={self.id!r}, platform_id={self.platform_id!r}, name={self.name!r}, platform={self.platform!r})"

class Video(Base):
    __tablename__ = "video"
    id: Mapped[int] = mapped_column(primary_key=True)
    original_name: Mapped[str] = mapped_column(String(255))

    author_id: Mapped[int] = mapped_column(ForeignKey("video_author.id"))
    author: Mapped["VideoAuthor"] = relationship(back_populates="videos")
    
    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"))
    file: Mapped["File"] = relationship(back_populates="video")

    request: Mapped["Request"] = relationship(back_populates="video", uselist=False)

    def __repr__(self) -> str:
        return f"Video(id={self.id!r}, original_name={self.original_name!r}, author_id={self.author_id!r}, file_id={self.file_id!r})"

    
class Request(Base):
    __tablename__ = "request"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, native_enum=False),
        default=RequestStatus.PENDING,
        nullable=False
    )
    type: Mapped[RequestType] = mapped_column(
        Enum(RequestType, native_enum=False),
        nullable=False
    )
    link: Mapped[str] = mapped_column(String(255))
    chat_id: Mapped[Optional[int]] = mapped_column()
    message_id: Mapped[str] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(String(255))
    error_details: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    user_account_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user_account: Mapped["User"] = relationship(back_populates="requests")

    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("video.id"))
    video: Mapped["Video"] = relationship(back_populates="request")
    
    def __repr__(self) -> str:
        return f"Request(id={self.id!r}, status={self.status!r}, type={self.type!r}, link={self.link!r}, chat_id={self.chat_id!r}, message_id={self.message_id!r}, error_message={self.error_message!r}, error_details={self.error_details!r}, created_at={self.created_at!r}, user_account_id={self.user_account_id!r}, video_id={self.video_id!r})"