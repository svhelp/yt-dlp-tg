from src.db.engine import engine
from src.db.schema import Base

Base.metadata.create_all(engine)
