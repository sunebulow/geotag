# Found Clothing Tag — Deploy Guide

## Filstruktur
```
project/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── found/[id]/index.html
│   └── vercel.json
└── generate_qr.py
```

---

## Trin 1 — Deploy backend til Railway

1. Gå til [railway.app](https://railway.app) og opret et nyt projekt
2. Vælg "Deploy from GitHub repo" og forbind dit GitHub repo
3. Railway registrerer automatisk Python — tilføj én environment variable:
   - `SURESMS_API_KEY` = din SureSMS API nøgle
4. Railway starter serveren automatisk med `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Kopier din Railway URL (fx `https://dit-projekt.railway.app`)

> **Vigtigt:** Tilføj en `Procfile` i `backend/` mappen med dette indhold:
> ```
> web: uvicorn main:app --host 0.0.0.0 --port $PORT
> ```

---

## Trin 2 — Opdater frontend med Railway URL

Åbn `frontend/found/[id]/index.html` og erstat:
```
const BACKEND_URL = "https://DIN-RAILWAY-URL.railway.app";
```
med din rigtige Railway URL.

---

## Trin 3 — Deploy frontend til Vercel

1. Gå til [vercel.com](https://vercel.com) og opret et nyt projekt
2. Forbind dit GitHub repo og sæt **Root Directory** til `frontend`
3. Klik Deploy
4. Kopier din Vercel URL (fx `https://dit-projekt.vercel.app`)

---

## Trin 4 — Generer QR koder

1. Installer qrcode biblioteket lokalt:
   ```
   pip install qrcode[pil]
   ```
2. Åbn `generate_qr.py` og erstat `DIN-VERCEL-URL` med din rigtige Vercel URL
3. Kør scriptet:
   ```
   python generate_qr.py
   ```
4. Du får to filer: `qr_sune.png` og `qr_pelle.png` — klar til print!

---

## Test

Scan en QR kode med din telefon → tillad lokation → tjek at Sune/Pelle modtager en SMS.

## SMS format
```
Hej [navn], dit glemte tøj er fundet og kan hentes her: [adresse], [Google Maps link]. Hilsen Prototypen
```
