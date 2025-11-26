import enum
from typing import List
from typing import Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy import DateTime
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

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    user_name: Mapped[str] = mapped_column(String(30))

    requests: Mapped[List["Request"]] = relationship(
        back_populates="user_account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, user_name={self.user_name!r})"
    
class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(100))

    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"))
    request: Mapped["Request"] = relationship(back_populates="file")

    def __repr__(self) -> str:
        return f"File(id={self.id!r}, path={self.path!r})"
    
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
    link: Mapped[str] = mapped_column(String(100))
    chat_id: Mapped[Optional[int]] = mapped_column()
    message_id: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    user_account_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))

    user_account: Mapped["User"] = relationship(back_populates="requests")
    file: Mapped["File"] = relationship(back_populates="request", uselist=False)
    
    def __repr__(self) -> str:
        return f"Request(id={self.id!r}, status={self.status!r})"