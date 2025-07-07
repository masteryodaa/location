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

app = FastAPI(
    title="Location Logger API",
    description="Collects location data and provides admin and web view",
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

# from fastapi.staticfiles import StaticFiles

# app.mount("/static", StaticFiles(directory="static"), name="static")

# Template setup
templates = Jinja2Templates(directory="templates")

# In-memory store
location_store = []

class LocationData(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: Optional[str] = None
    userAgent: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """
    Renders the landing page (index.html)
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/locations")
@limiter.limit("100/15minutes")
async def store_location(request: Request, data: LocationData):
    if data.latitude is None or data.longitude is None:
        raise HTTPException(status_code=400, detail="Missing required fields")
    rec = {
        "id": str(uuid4()),
        "latitude": data.latitude,
        "longitude": data.longitude,
        "accuracy": data.accuracy,
        "timestamp": data.timestamp or datetime.utcnow().isoformat(),
        "userAgent": data.userAgent,
        "ipAddress": request.client.host,
        "createdAt": datetime.utcnow().isoformat()
    }
    location_store.append(rec)
    print("Stored location:", rec)
    return JSONResponse(status_code=201, content={
        "success": True,
        "message": "Location stored successfully",
        "redirectUrl": rec["redirectUrl"] if "redirectUrl" in rec else None
    })

@app.get("/admin/locations")
async def admin_locations():
    """
    Raw JSON admin endpoint for seeing stored locations
    """
    return {"count": len(location_store), "locations": location_store}

@app.get("/view-locations", response_class=HTMLResponse)
async def view_locations(request: Request):
    """
    Renders a webpage listing all stored locations
    """
    return templates.TemplateResponse(
        "view_locations.html",
        {"request": request, "locations": location_store}
    )
