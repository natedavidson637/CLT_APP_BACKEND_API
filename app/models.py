from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Float,
    DateTime, Text, JSON, ARRAY
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


# ============================================================
# USERS MODULE
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password_hash = Column(String)
    age = Column(Integer)
    gender = Column(String)
    bio = Column(Text, nullable=True)
    interests = Column(ARRAY(String), nullable=True)
    profile_visibility = Column(String, default="public")
    fcm_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    followers = relationship(
        "Follower",
        foreign_keys="Follower.following_id",
        back_populates="following_user"
    )

    following = relationship(
        "Follower",
        foreign_keys="Follower.follower_id",
        back_populates="follower_user"
    )


class Follower(Base):
    __tablename__ = "followers"

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey("users.id"))
    following_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    follower_user = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following_user = relationship("User", foreign_keys=[following_id], back_populates="followers")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    allow_messages = Column(Boolean, default=True)
    allow_event_invites = Column(Boolean, default=True)
    allow_club_invites = Column(Boolean, default=True)
    dark_mode = Column(Boolean, default=False)
    location_services_enabled = Column(Boolean, default=True)


# ============================================================
# EVENTS MODULE
# ============================================================

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text)
    gps_lat = Column(Float)
    gps_lon = Column(Float)
    address = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    capacity_limit = Column(Integer, nullable=True)
    price = Column(Integer, nullable=True)
    visibility = Column(String, default="public")
    tags = Column(ARRAY(String))
    media_cover_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    rsvps = relationship("EventRSVP", back_populates="event")
    media = relationship("EventMedia", back_populates="event")


class EventRSVP(Base):
    __tablename__ = "event_rsvp"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)  # going / waitlist / paid / cancelled
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="rsvps")


class EventMedia(Base):
    __tablename__ = "event_media"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    media_url = Column(String)
    media_type = Column(String)  # image / video
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="media")


class EventAnalytics(Base):
    __tablename__ = "event_analytics"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    avg_age = Column(Float)
    gender_distribution = Column(JSON)
    total_rsvps = Column(Integer)
    total_views = Column(Integer)
    total_shares = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# PAYMENTS MODULE
# ============================================================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_session_id = Column(String)
    amount = Column(Integer)
    status = Column(String)  # pending / paid / refunded / failed
    created_at = Column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    qr_code_url = Column(String)
    checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime, nullable=True)


# ============================================================
# CHAT MODULE
# ============================================================

class EventChatRoom(Base):
    __tablename__ = "event_chat_rooms"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class EventChatMessage(Base):
    __tablename__ = "event_chat_messages"

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("event_chat_rooms.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    message_text = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)


class EventChatAdmin(Base):
    __tablename__ = "event_chat_admins"

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("event_chat_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))


# ============================================================
# CLUBS MODULE
# ============================================================

class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text)
    school = Column(String, nullable=True)
    visibility = Column(String, default="public")
    created_at = Column(DateTime, default=datetime.utcnow)


class ClubMember(Base):
    __tablename__ = "club_members"

    id = Column(Integer, primary_key=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # member / admin
    joined_at = Column(DateTime, default=datetime.utcnow)


class ClubEvent(Base):
    __tablename__ = "club_events"

    id = Column(Integer, primary_key=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    event_id = Column(Integer, ForeignKey("events.id"))


# ============================================================
# FEED MODULE (TikTok-style)
# ============================================================

class FeedPost(Base):
    __tablename__ = "feed_posts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    video_url = Column(String)
    thumbnail_url = Column(String)
    caption = Column(Text)
    tags = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedLike(Base):
    __tablename__ = "feed_likes"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("feed_posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedView(Base):
    __tablename__ = "feed_views"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("feed_posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedComment(Base):
    __tablename__ = "feed_comments"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("feed_posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrendingScore(Base):
    __tablename__ = "trending_scores"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("feed_posts.id"))
    score = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# REVIEWS MODULE
# ============================================================

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_type = Column(String)  # event / location / restaurant
    target_id = Column(Integer)
    rating = Column(Integer)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# SAFETY MODULE
# ============================================================

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    target_type = Column(String)  # user / event / post
    target_id = Column(Integer)
    reason = Column(String)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class BlockedUser(Base):
    __tablename__ = "blocked_users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    blocked_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
