import enum
from typing import List
from typing import Optional
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

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

    requests: Mapped[List["Request"]] = relationship(
        back_populates="user_account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"
    
class Chat(Base):
    __tablename__ = "chat"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"))
    request: Mapped["Request"] = relationship(back_populates="chat", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Chat(id={self.id!r}, name={self.name!r})"

class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(50))
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
    user_account_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id"))
    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"))

    user_account: Mapped["User"] = relationship(back_populates="requests")
    chat: Mapped["Chat"] = relationship(back_populates="request")
    file: Mapped["File"] = relationship(back_populates="request", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"Request(id={self.id!r}, status={self.status!r})"