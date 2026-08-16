print(">>> USING UPDATED MAIN.PY <<<")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Charlotte Core API",
    description="Backend powering Charlotte-wide events, clubs, chat, feed, payments, and discovery.",
    version="1.0.0"
)

# ------------------------------------------------------------
# CORS MUST COME BEFORE ROUTER IMPORTS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://kindred-roots-api.lovable.app",
        "https://*.lovable.app",
        "https://web-production-6ac00e.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# NOW IMPORT ROUTERS
# ------------------------------------------------------------
from .routers import (
    auth,
    users,
    events,
    rsvp,
    payments,
    chat,
    clubs,
    feed,
    reviews,
    safety
)

# ------------------------------------------------------------
# REGISTER ROUTERS
# ------------------------------------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(rsvp.router)
app.include_router(payments.router)
app.include_router(chat.router)
app.include_router(clubs.router)
app.include_router(feed.router)
app.include_router(reviews.router)
app.include_router(safety.router)

# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Charlotte Core API is running"}

@app.options("/{full_path:path}")
def preflight_handler():
    return {}
