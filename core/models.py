from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from .utils import shrink, webp_name, wa_link

HOUSE_TYPES = [(t, t) for t in ["Single room", "Bedsitter", "Studio", "One bedroom", "Two bedroom", "Three bedroom", "Shared accommodation", "Other"]]
AMENITIES = [("wifi", "Wi-Fi"), ("water", "Reliable water"), ("electricity", "Electricity"), ("parking", "Parking"),
             ("security", "Security guard"), ("cctv", "CCTV"), ("furnished", "Furnished"), ("own_compound", "Own compound"),
             ("balcony", "Balcony"), ("kitchen", "Kitchen"), ("laundry", "Laundry area"),
             ("pet_friendly", "Pet-friendly"), ("shared_compound", "Shared compound"),
             ("tiles", "Tiles"), ("fans", "Fans"), ("ceiling", "Ceiling"), ("wardrobe", "Wardrobe"), ("ac", "Air conditioning")]


class Institution(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    def __str__(self): return self.name


class Property(models.Model):
    STATUS = [("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")]
    VERIF = [("landlord", "Landlord listed"), ("pending", "Pending verification"), ("verified", "AMOX Verified"), ("partner", "Partner property")]
    title = models.CharField(max_length=140)
    slug = models.SlugField(unique=True, blank=True, max_length=180)
    owner_name = models.CharField(max_length=120)
    owner_phone = models.CharField(max_length=30)
    owner_email = models.EmailField(blank=True)
    area = models.CharField(max_length=100, help_text="Town/area, e.g. Malindi Town")
    estate = models.CharField(max_length=100, blank=True)
    house_type = models.CharField(max_length=40, choices=HOUSE_TYPES)
    rent = models.PositiveIntegerField("Monthly rent (KSh)")
    deposit = models.PositiveIntegerField("Deposit (KSh)", default=0)
    units_total = models.PositiveIntegerField(default=1)
    units_vacant = models.PositiveIntegerField(default=1)
    description = models.TextField()
    environment = models.TextField("Around the house", blank=True, help_text="Neighbourhood, shops, transport, noise")
    wifi = models.BooleanField("Wi-Fi", default=False)
    water = models.BooleanField("Reliable water", default=False)
    electricity = models.BooleanField(default=True)
    parking = models.BooleanField(default=False)
    security = models.BooleanField("Security guard", default=False)
    cctv = models.BooleanField("CCTV", default=False)
    furnished = models.BooleanField(default=False)
    own_compound = models.BooleanField(default=False)
    balcony = models.BooleanField(default=False)
    kitchen = models.BooleanField(default=False)
    laundry = models.BooleanField("Laundry area", default=False)
    pet_friendly = models.BooleanField("Pet-friendly", default=False)
    shared_compound = models.BooleanField(default=False)
    tiles = models.BooleanField("Tiles", default=False)
    fans = models.BooleanField("Fans", default=False)
    ceiling = models.BooleanField("Ceiling", default=False)
    wardrobe = models.BooleanField("Wardrobe", default=False)
    ac = models.BooleanField("Air conditioning", default=False)
    nearby_institutions = models.CharField("Nearby schools / colleges", max_length=200, blank=True, default="", help_text="e.g. MKU Malindi, Malindi High School")
    nearby_hospitals = models.CharField("Nearby hospitals / clinics", max_length=200, blank=True, default="")
    nearby_shops = models.CharField("Nearby shops / markets", max_length=200, blank=True, default="")
    nearby_transport = models.CharField("Transport and roads", max_length=200, blank=True, default="", help_text="e.g. Matatu stage 300 m, tarmac road")
    nearby_landmarks = models.CharField("Other landmarks", max_length=200, blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    verification = models.CharField(max_length=10, choices=VERIF, default="landlord")
    verified_on = models.DateField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "properties"
        ordering = ["-featured", "-created_at"]

    def __str__(self): return f"{self.title} ({self.area})"
    def get_absolute_url(self): return reverse("property_detail", args=[self.slug])

    def save(self, *a, **k):
        if not self.slug:
            base = slugify(f"{self.title} {self.area}")[:160]; slug, n = base, 2
            while Property.objects.filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*a, **k)

    @property
    def amenity_list(self): return [label for f, label in AMENITIES if getattr(self, f)]
    @property
    def nearby(self):
        rows = [("Schools and colleges", self.nearby_institutions), ("Hospitals", self.nearby_hospitals),
                ("Shops and markets", self.nearby_shops), ("Transport and roads", self.nearby_transport), ("Landmarks", self.nearby_landmarks)]
        return [(k, v) for k, v in rows if v]
    @property
    def is_verified(self): return self.verification == "verified"
    @property
    def cover(self):
        return next((m for m in self.media.all() if m.kind == "photo" and m.thumb), None)


class PropertyMedia(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField(max_length=5, choices=[("photo", "Photo"), ("video", "Video")], default="photo")
    section = models.CharField(max_length=6, choices=[("inside", "Inside the house"), ("around", "Around the house")], default="inside")
    file = models.FileField(upload_to="properties/%Y/%m/")
    thumb = models.ImageField(upload_to="thumbs/%Y/%m/", blank=True, editable=False)

    def save(self, *a, **k):
        if self.kind == "photo" and not self.pk:  # compress + thumbnail on first upload
            raw = self.file.read(); self.file.seek(0)
            name = webp_name(self.file.name)
            self.file.save(name, shrink(raw, 1400), save=False)
            self.thumb.save(name, shrink(raw, 480, 68), save=False)
        super().save(*a, **k)


class Distance(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="distances")
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    km = models.DecimalField(max_digits=5, decimal_places=1)
    class Meta:
        unique_together = ("property", "institution")
        ordering = ["km"]


class Lead(models.Model):
    KINDS = [("house", "House request"), ("inquiry", "Property inquiry"), ("internet", "Internet"), ("gas", "Gas cylinder"),
             ("items", "Mattress / household"), ("moving", "Relocation"), ("other", "Other service"), ("general", "General enquiry")]
    STATUS = [("new", "New"), ("contacted", "Contacted"), ("suggested", "House suggested"), ("viewing", "Viewing arranged"),
              ("connected", "Connected"), ("completed", "Completed"), ("closed", "Closed")]
    kind = models.CharField(max_length=10, choices=KINDS)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    details = models.JSONField(default=dict, blank=True)
    property = models.ForeignKey(Property, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, choices=STATUS, default="new")
    notes = models.TextField(blank=True, help_text="Internal notes")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"Lead {self.pk}: {self.get_kind_display()} - {self.name}"

    def wa_text(self):
        lines = [f"*{self.get_kind_display()}* (ref {self.pk})", f"Name: {self.name}", f"Phone: {self.phone}"]
        if self.property: lines.append(f"House: {self.property.title}")
        lines += [f"{k}: {v}" for k, v in self.details.items()]
        return "\n".join(lines)
    def wa_link(self): return wa_link(self.wa_text())


class ServiceProvider(models.Model):
    CATS = [("internet", "Internet/Wi-Fi"), ("gas", "Gas"), ("items", "Mattress & household items"), ("moving", "Moving"), ("other", "Other")]
    name = models.CharField("Contact name", max_length=120)
    business = models.CharField(max_length=140)
    category = models.CharField(max_length=10, choices=CATS)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    coverage = models.CharField(max_length=200, blank=True)
    details = models.TextField("Packages, prices, notes", blank=True)
    package = models.CharField("Package name", max_length=80, blank=True, default="")
    speed = models.CharField(max_length=40, blank=True, default="", help_text="e.g. 10 Mbps")
    price = models.CharField("Price", max_length=60, blank=True, default="", help_text="e.g. KSh 2,500/month")
    install_fee = models.CharField("Installation fee", max_length=60, blank=True, default="")
    commission_pct = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    status = models.CharField(max_length=10, choices=[("pending", "Pending"), ("approved", "Approved"), ("suspended", "Suspended")], default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.business


class SearchLog(models.Model):
    """One row per search by area/institution, used for 'most searched locations'."""
    term = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.term


def _safe_link(v):
    v = (v or "").strip()
    return v if (v.startswith("/") and not v.startswith("//")) or v.lower().startswith(("http://", "https://")) else ""

def validate_link(v):
    from django.core.exceptions import ValidationError
    if v and not _safe_link(v): raise ValidationError("Use a page like /houses/ or a full web address starting with https://")

class Announcement(models.Model):
    """News / announcements shown in the scrolling strip under the homepage hero."""
    text = models.CharField(max_length=140)
    link = models.CharField("Link (optional)", max_length=200, blank=True, validators=[validate_link], help_text="A page like /houses/ or a full web address")
    is_active = models.BooleanField("Show on website", default=True)
    expires_on = models.DateField("Hide after", null=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["order", "-created_at"]
    def __str__(self): return self.text
    @property
    def safe_link(self): return _safe_link(self.link)
    @classmethod
    def live(cls):
        from django.utils import timezone
        today = timezone.localdate()
        return cls.objects.filter(is_active=True).filter(models.Q(expires_on__isnull=True) | models.Q(expires_on__gte=today))
