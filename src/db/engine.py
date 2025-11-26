import src.config
import os

from sqlalchemy import create_engine

host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

connection_string = f"mysql+pymysql://{username}:{password}@{host}:3306/{db_name}"

print(f"Connecting to DB: {connection_string}")

engine = create_engine(connection_string, echo=True)
