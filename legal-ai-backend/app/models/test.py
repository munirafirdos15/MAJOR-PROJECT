from sqlalchemy import Column, Integer
from app.db.database import Base


class Test(Base):
    __tablename__ = "test"

    id = Column(Integer, primary_key=True)
