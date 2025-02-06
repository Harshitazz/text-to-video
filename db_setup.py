from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base  # Updated import
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
POSTGRES_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(
    POSTGRES_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class using new syntax
Base = declarative_base()  # Now imported from sqlalchemy.orm

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Video Metadata Model
class VideoMetadata(Base):
    __tablename__ = "video_metadata"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    tags = Column(JSON)
    video_url = Column(String)
    youtube_video_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<VideoMetadata(id={self.id}, title='{self.title}')>"

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()