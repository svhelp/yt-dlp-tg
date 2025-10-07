import src.config
import os

from sqlalchemy import create_engine

host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

engine = create_engine(
    f"mysql+pymysql://{username}:{password}@{host}:3306/{db_name}",
    echo=True
)
