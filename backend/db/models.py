from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./fitfinder.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ClothingItem(Base):
    __tablename__ = "clothing_items"
    id = Column(String, primary_key=True, index=True)
    description = Column(Text)
    image_url = Column(String)
    tags = Column(Text)  # Comma-separated for now
