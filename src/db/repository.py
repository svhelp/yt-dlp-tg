from typing import Optional
from datetime import datetime, date, timedelta

from src.db.engine import engine
from src.db.schema import User, File, Request, Video, RequestStatus, RequestType, VideoAuthor

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select, func

SessionLocal = sessionmaker(engine, expire_on_commit=False)

def get_or_create_user(id: int, name: str, username: str):
    with Session(engine) as session:
        user = session.get(User, id)
        if not user:
            user = User(
                id=id,
                name=name,
                username=username
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        return user
    
def get_today_requests_count(user_id: int):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    with Session(engine) as session:
        count = session.scalar(
            select(func.count())
            .where(Request.user_account_id == user_id)
            .where(Request.created_at >= today)
            .where(Request.created_at < tomorrow)
        )

        return count
    
def create_request(user_id: int, type: RequestType, link: str, message_id: str, chat_id: Optional[int] = None):
    with Session(engine) as session:        
        request_data = dict(
            message_id=message_id,
            status=RequestStatus.PENDING,
            type=type,
            link=link,
            user_account_id=user_id,
        )

        if chat_id is not None:
            request_data["chat_id"] = chat_id

        request = Request(**request_data)

        session.add(request)
        session.commit()
        session.refresh(request)

        return request

def set_request_successful(request_id: int):
    with Session(engine) as session:
        session.query(Request).filter(Request.id == request_id).update({Request.status: RequestStatus.SUCCESSFUL})
        session.commit()

def set_request_error(request_id: int, error_message: str, error_details: Optional[str] = None):
    with Session(engine) as session:
        request_data = dict(
            status=RequestStatus.FAILED,
            error_message=error_message,
        )

        if error_details is not None:
            request_data["error_details"] = error_details

        update_data = {k: v for k, v in request_data.items() if v is not None}

        session.query(Request).filter(Request.id == request_id).update(update_data)
        session.commit()

def create_file_data(request: Request, path: str, title: str, platform: str, platform_id: str, author_name: str):
    with Session(engine) as session:
        file = File(
            path = path
        )
        session.add(file)  

        author = session.query(VideoAuthor).filter(VideoAuthor.platform == platform and VideoAuthor.platform_id == platform_id).first()
        if not author:
            author = VideoAuthor(
                platform = platform,
                platform_id = platform_id,
                name = author_name,
            )
            session.add(author)    
            
        video = Video(
            original_name = title,
            author = author,
            file = file,
            requests = [
                request,
            ]
        )
        session.add(video)
        
        session.commit()