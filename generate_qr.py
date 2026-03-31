"""
Kør dette script lokalt for at generere QR koder til Sune og Pelle.
Kræver: pip install qrcode[pil]

Erstat VERCEL_URL med din rigtige Vercel URL inden du kører scriptet.
"""

import qrcode

VERCEL_URL = "https://DIN-VERCEL-URL.vercel.app"

profiles = ["sune", "pelle"]

for profile_id in profiles:
    url = f"{VERCEL_URL}/found/{profile_id}"
    qr = qrcode.make(url)
    filename = f"qr_{profile_id}.png"
    qr.save(filename)
    print(f"✓ QR kode gemt: {filename} -> {url}")

print("\nFærdig! Print QR koderne og sæt dem på navne-taggene.")
