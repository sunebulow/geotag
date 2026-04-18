from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import httpx
import os
import urllib.parse
import secrets
import random
import string
import asyncpg

app = FastAPI()
security = HTTPBasic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
SURESMS_API_KEY = os.environ.get("SURESMS_API_KEY", "")


# --- Database setup ---

async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()


@app.on_event("startup")
async def startup():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id VARCHAR(6) PRIMARY KEY,
            phone VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    await conn.close()


# --- Auth ---

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forkert password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


# --- Helpers ---

def generate_id() -> str:
    return ''.join(random.choices(string.digits, k=6))


async def reverse_geocode(lat: float, lon: float) -> dict:
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    headers = {"User-Agent": "GeoTag/1.0"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
        addr = data.get("address", {})
        road = addr.get("road", "")
        house_number = addr.get("house_number", "")
        postcode = addr.get("postcode", "")
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        formatted = f"{road} {house_number}, {postcode}, {city}".strip(", ")
        return formatted


async def send_sms(phone: str, message: str):
    if not SURESMS_API_KEY:
        raise Exception("SURESMS_API_KEY er ikke sat")
    encoded_message = urllib.parse.quote(message)
    url = (
        f"https://api.suresms.com/Script/SendSMS.aspx"
        f"?login=apikey"
        f"&password={SURESMS_API_KEY}"
        f"&to={phone}"
        f"&Text={encoded_message}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise Exception(f"SureSMS fejl: {response.text}")
        return response.text


# --- Models ---

class CreateCustomerPayload(BaseModel):
    phone: str


class LocationPayload(BaseModel):
    customer_id: str
    latitude: float
    longitude: float


# --- Endpoints ---

@app.post("/customers")
async def create_customer(payload: CreateCustomerPayload):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Generer unikt 6-cifret ID
        for _ in range(10):
            new_id = generate_id()
            existing = await conn.fetchrow("SELECT id FROM customers WHERE id = $1", new_id)
            if not existing:
                break
        await conn.execute(
            "INSERT INTO customers (id, phone) VALUES ($1, $2)",
            new_id, payload.phone
        )
        return {"id": new_id, "phone": payload.phone}
    finally:
        await conn.close()


@app.get("/admin/customers")
async def list_customers(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("SELECT id, phone, created_at FROM customers ORDER BY created_at DESC")
        return [{"id": r["id"], "phone": r["phone"], "created_at": str(r["created_at"])} for r in rows]
    finally:
        await conn.close()


@app.post("/found/{customer_id}")
async def found_item(customer_id: str, payload: LocationPayload):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT phone FROM customers WHERE id = $1", customer_id)
        if not row:
            raise HTTPException(status_code=404, detail="Kunde ikke fundet")

        address = await reverse_geocode(payload.latitude, payload.longitude)
        maps_link = f"https://maps.google.com/?q={payload.latitude},{payload.longitude}"

        message = (
            f"Hej! Din glemte ejendel er fundet og kan hentes her: "
            f"{address}. Google Maps: {maps_link}. Hilsen Geotag"
        )

        await send_sms(row["phone"], message)
        return {"status": "ok"}
    finally:
        await conn.close()


@app.get("/health")
async def health():
    return {"status": "ok"}
