from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import time

# Load .env if running locally
if os.path.exists(".env"):
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")

# Retry loop so Railway doesn't crash if Postgres isn't ready yet
engine = None
for i in range(10):
    try:
        print(f"Connecting to database... attempt {i+1}/10")

        # ⭐ ADD TIMEOUT HERE — this is the fix
        engine = create_engine(
            DATABASE_URL,
            connect_args={"connect_timeout": 5}
        )

        conn = engine.connect()
        conn.close()

        print("Database connection successful.")
        break

    except Exception as e:
        print(f"Database not ready, retrying in 2 seconds... ({e})")
        time.sleep(2)

if engine is None:
    raise RuntimeError("Could not connect to the database after multiple attempts.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from app.models import (
    User,
    Follower,
    UserSettings,
    Event,
    EventRSVP,
    EventMedia,
    EventAnalytics,
    Payment,
    Ticket,
    EventChatRoom,
    EventChatMessage,
    EventChatAdmin,
    Club,
    ClubMember,
    ClubEvent,
    FeedPost,
    FeedLike,
    FeedView,
    FeedComment,
    TrendingScore,
    Review,
    Report,
    BlockedUser
)

Base.metadata.create_all(bind=engine)