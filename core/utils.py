import os
from io import BytesIO
from urllib.parse import quote
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

def wa_link(text=""):
    return f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(text)}"

def shrink(raw, size, quality=72):
    """Resize to fit size x size and return a WebP ContentFile (small for low-data users)."""
    im = ImageOps.exif_transpose(Image.open(BytesIO(raw))).convert("RGB")
    im.thumbnail((size, size))
    out = BytesIO()
    im.save(out, "WEBP", quality=quality, method=6)
    return ContentFile(out.getvalue())

def webp_name(name):
    return os.path.splitext(os.path.basename(name))[0] + ".webp"

def notify(subject, body):
    """Email the AMOX team. Never breaks the page if email is not configured."""
    from django.core.mail import send_mail
    try:
        send_mail(f"[AMOXHomes] {subject}", body, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL], fail_silently=True)
    except Exception:
        pass
