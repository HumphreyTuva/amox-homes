"""Prepare the service photos for the website.

Reads the photos in  media/service-images/  (bed, gas, internet, move, service - any image type),
and writes small WebP copies into  core/static/core/services/  where the site serves them from.

Run once from the project root:
    python tools/optimize_service_images.py
"""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "media" / "service-images"
DST = ROOT / "core" / "static" / "core" / "services"
# photo name -> service key used by the site
NAMES = {"internet": "internet", "gas": "gas", "bed": "items", "move": "moving", "service": "other"}

DST.mkdir(parents=True, exist_ok=True)
for name, key in NAMES.items():
    found = [f for f in SRC.iterdir() if f.is_file() and f.stem.lower() == name] if SRC.exists() else []
    if not found:
        print(f"MISSING  {name}.* not found in {SRC}")
        continue
    img = ImageOps.exif_transpose(Image.open(found[0])).convert("RGB")
    img = ImageOps.fit(img, (640, 400), Image.LANCZOS)          # same shape for every card
    out = DST / f"{key}.webp"
    img.save(out, "WEBP", quality=72, method=6)
    print(f"OK       {found[0].name} -> {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
