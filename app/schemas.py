from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

# ============================================================
# USERS MODULE
# ============================================================

class UserBase(BaseModel):
    name: str
    email: str
    age: Optional[int]
    gender: Optional[str]
    bio: Optional[str]
    interests: Optional[List[str]]
    profile_visibility: Optional[str] = "public"


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int]
    gender: Optional[str]
    bio: Optional[str]
    interests: Optional[List[str]]
    profile_visibility: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



class Follower(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class UserSettings(BaseModel):
    id: int
    user_id: int
    allow_messages: bool
    allow_event_invites: bool
    allow_club_invites: bool
    dark_mode: bool
    location_services_enabled: bool

    class Config:
        orm_mode = True


# ============================================================
# EVENTS MODULE
# ============================================================

class EventBase(BaseModel):
    title: str
    description: str
    gps_lat: float
    gps_lon: float
    address: str
    start_time: datetime
    end_time: datetime
    age_min: Optional[int]
    age_max: Optional[int]
    capacity_limit: Optional[int]
    price: Optional[int]
    visibility: str = "public"
    tags: Optional[List[str]]


class EventCreate(EventBase):
    creator_id: int


class Event(EventBase):
    id: int
    media_cover_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class EventRSVPBase(BaseModel):
    event_id: int
    user_id: int
    status: str


class EventRSVP(EventRSVPBase):
    id: int
    payment_id: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True


class EventMediaBase(BaseModel):
    event_id: int
    media_url: str
    media_type: str


class EventMedia(EventMediaBase):
    id: int
    uploaded_by: int
    created_at: datetime

    class Config:
        orm_mode = True


class EventAnalytics(BaseModel):
    id: int
    event_id: int
    avg_age: float
    gender_distribution: dict
    total_rsvps: int
    total_views: int
    total_shares: int
    updated_at: datetime

    class Config:
        orm_mode = True


# ============================================================
# PAYMENTS MODULE
# ============================================================

class PaymentBase(BaseModel):
    event_id: int
    user_id: int
    amount: int


class Payment(PaymentBase):
    id: int
    stripe_session_id: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class Ticket(BaseModel):
    id: int
    payment_id: int
    event_id: int
    user_id: int
    qr_code_url: str
    checked_in: bool
    checked_in_at: Optional[datetime]

    class Config:
        orm_mode = True


# ============================================================
# CHAT MODULE
# ============================================================

class EventChatRoom(BaseModel):
    id: int
    event_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class EventChatMessageBase(BaseModel):
    room_id: int
    sender_id: int
    message_text: Optional[str]
    media_url: Optional[str]


class EventChatMessage(EventChatMessageBase):
    id: int
    timestamp: datetime
    is_deleted: bool
    is_pinned: bool

    class Config:
        orm_mode = True


class EventChatAdmin(BaseModel):
    id: int
    room_id: int
    user_id: int

    class Config:
        orm_mode = True


# ============================================================
# CLUBS MODULE
# ============================================================

class ClubBase(BaseModel):
    name: str
    description: str
    school: Optional[str]
    visibility: str = "public"


class ClubCreate(ClubBase):
    creator_id: int


class Club(ClubBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ClubMember(BaseModel):
    id: int
    club_id: int
    user_id: int
    role: str
    joined_at: datetime

    class Config:
        orm_mode = True


class ClubEvent(BaseModel):
    id: int
    club_id: int
    event_id: int

    class Config:
        orm_mode = True


# ============================================================
# FEED MODULE
# ============================================================

class FeedPostBase(BaseModel):
    user_id: int
    event_id: Optional[int]
    video_url: str
    thumbnail_url: str
    caption: str
    tags: Optional[List[str]]


class FeedPost(FeedPostBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class FeedLike(BaseModel):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class FeedView(BaseModel):
    id: int
    post_id: int
    user_id: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True


class FeedComment(BaseModel):
    id: int
    post_id: int
    user_id: int
    text: str
    created_at: datetime

    class Config:
        orm_mode = True


class TrendingScore(BaseModel):
    id: int
    post_id: int
    score: float
    updated_at: datetime

    class Config:
        orm_mode = True


# ============================================================
# REVIEWS MODULE
# ============================================================

class ReviewBase(BaseModel):
    target_type: str
    target_id: int
    rating: int
    text: str


class Review(ReviewBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ============================================================
# SAFETY MODULE
# ============================================================

class ReportBase(BaseModel):
    target_type: str
    target_id: int
    reason: str
    details: str


class Report(ReportBase):
    id: int
    reporter_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class BlockedUser(BaseModel):
    id: int
    user_id: int
    blocked_user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
