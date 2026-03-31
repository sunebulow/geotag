from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Hardcodede profiler til prototypen
PROFILES = {
    "sune": {
        "name": "Sune",
        "phone": "+4520700268",
    },
    "pelle": {
        "name": "Pelle",
        "phone": "+4553612741",
    },
}


class LocationPayload(BaseModel):
    profile_id: str
    latitude: float
    longitude: float


async def reverse_geocode(lat: float, lon: float) -> str:
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    headers = {"User-Agent": "FoundClothingTag/1.0"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
        return data.get("display_name", f"{lat}, {lon}")


async def send_sms(phone: str, message: str):
    api_key = os.environ.get("SURESMS_API_KEY")
    if not api_key:
        raise Exception("SURESMS_API_KEY er ikke sat")
    encoded_message = urllib.parse.quote(message)
    url = (
        f"https://api.suresms.com/Script/SendSMS.aspx"
        f"?login=apikey"
        f"&password={api_key}"
        f"&to={phone}"
        f"&Text={encoded_message}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise Exception(f"SureSMS fejl: {response.text}")
        return response.text


@app.post("/found/{profile_id}")
async def found_item(profile_id: str, payload: LocationPayload):
    profile = PROFILES.get(profile_id.lower())
    if not profile:
        raise HTTPException(status_code=404, detail="Profil ikke fundet")

    address = await reverse_geocode(payload.latitude, payload.longitude)
    maps_link = f"https://maps.google.com/?q={payload.latitude},{payload.longitude}"

    message = (
        f"Hej {profile['name']}, dit glemte tøj er fundet og kan hentes her: "
        f"{address}, {maps_link}. Hilsen Prototypen"
    )

    await send_sms(profile["phone"], message)

    return {"status": "ok", "message": "SMS sendt"}


@app.get("/health")
async def health():
    return {"status": "ok"}
