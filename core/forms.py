from django import forms
from .models import Property, ServiceProvider, Institution, HOUSE_TYPES, AMENITIES

CLS = "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky"

# Fields remembered on the visitor's own device (browser only) so repeat forms are prefilled.
PF = {"name": "name", "owner_name": "name", "phone": "phone", "owner_phone": "phone", "email": "email", "owner_email": "email",
      "location": "location", "institution": "institution", "budget": "budget", "house_type": "house_type",
      "furnished": "furnished", "move_in": "move_in"}
AC = {"name": "name", "owner_name": "name", "email": "email", "owner_email": "email"}

class Styled:
    more = ()          # optional fields tucked behind "Add more details"
    no_prefill = ()
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        for n, f in self.fields.items():
            if n in PF and n not in self.no_prefill: f.widget.attrs["data-pf"] = PF[n]
            if n in AC: f.widget.attrs["autocomplete"] = AC[n]
            if n.endswith("phone"): f.widget.input_type = "tel"; f.widget.attrs.update(inputmode="tel", autocomplete="tel")
            f.widget.attrs["class"] = "h-5 w-5" if isinstance(f.widget, forms.CheckboxInput) else CLS
            if isinstance(f.widget, forms.Textarea): f.widget.attrs["rows"] = 3

class LeadForm(Styled, forms.Form):
    name = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=30, label="Phone / WhatsApp")

class HouseForm(LeadForm):
    institution = forms.ModelChoiceField(Institution.objects.all(), required=False, empty_label="Other", label="Institution or workplace")
    location = forms.CharField(required=False, label="Preferred area")
    house_type = forms.ChoiceField(choices=HOUSE_TYPES)
    budget = forms.CharField(label="Budget (KSh per month)", help_text="e.g. 6,000 - 8,000")
    move_in = forms.DateField(required=False, label="Move-in date", widget=forms.DateInput(attrs={"type": "date"}))
    furnished = forms.ChoiceField(required=False, choices=[("Either", "Either"), ("Furnished", "Furnished"), ("Unfurnished", "Unfurnished")])
    more = ("move_in", "furnished", "notes")
    notes = forms.CharField(required=False, label="Special requirements", widget=forms.Textarea)

class InternetForm(LeadForm):
    location = forms.CharField()
    wifi_type = forms.ChoiceField(choices=[("Home Wi-Fi", "Home Wi-Fi"), ("Hotspot", "Hotspot")], label="Type")
    budget = forms.CharField(required=False, label="Budget (KSh per month)")
    more = ("budget",)

class GasForm(LeadForm):
    location = forms.CharField()
    cylinder_size = forms.ChoiceField(choices=[("6 kg", "6 kg"), ("13 kg", "13 kg")])
    duration = forms.ChoiceField(choices=[(d, d) for d in ["1 month", "3 months", "Semester", "Longer"]])
    delivery = forms.ChoiceField(choices=[("Deliver to me", "Deliver to me"), ("I will pick up", "I will pick up")])

class ItemsForm(LeadForm):
    location = forms.CharField()
    items = forms.CharField(label="Items needed", widget=forms.Textarea, help_text="Mattress, bed, chairs, table, curtains, kitchen items")
    option = forms.ChoiceField(choices=[(o, o) for o in ["Hire", "Buy", "Either"]])

class MovingForm(LeadForm):
    pickup = forms.CharField(label="Pickup location")
    destination = forms.CharField()
    moving_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    load = forms.ChoiceField(choices=[(o, o) for o in ["A few bags", "Room contents", "1 bedroom", "2+ bedrooms"]], label="Amount of items")
    notes = forms.CharField(required=False, label="Special requirements", widget=forms.Textarea)
    more = ("notes",)

class OtherForm(LeadForm):
    service = forms.ChoiceField(choices=[(o, o) for o in ["Water refill", "Furniture", "Cleaning / laundry", "Repairs", "Security (CCTV)", "Groceries", "Other"]])
    details = forms.CharField(widget=forms.Textarea)

class ContactForm(LeadForm):
    topic = forms.ChoiceField(choices=[(o, o) for o in ["General enquiry", "Report a listing", "Report a landlord", "Partnership"]])
    message = forms.CharField(widget=forms.Textarea)

class InquiryForm(LeadForm):
    move_in = forms.DateField(required=False, label="Move-in date", widget=forms.DateInput(attrs={"type": "date"}))
    message = forms.CharField(required=False, widget=forms.Textarea)
    more = ("move_in", "message")

# kind -> (title, intro, icon, form)
SERVICES = {
    "house": ("Help me find a house", "Tell us what you need. We suggest suitable houses on WhatsApp.", "🏠", HouseForm),
    "internet": ("Need internet? We've got you connected", "We link you to a provider that covers your area.", "📶", InternetForm),
    "gas": ("Gas cylinder hire", "Cylinder, cooker and delivery arranged for you.", "🔥", GasForm),
    "items": ("Move in without buying everything", "Hire or buy a mattress and basic household items.", "🛏️", ItemsForm),
    "moving": ("Moving to Malindi? Let us help you move", "We connect you to an approved mover.", "🚚", MovingForm),
    "other": ("More settlement services", "Water refills, furniture, cleaning, repairs, security and more.", "🧰", OtherForm),
}

def _video_ok(f):
    if not f.name.lower().endswith((".mp4", ".webm", ".mov")) or f.size > 30 * 1024 * 1024:
        raise forms.ValidationError("Use an MP4, WebM or MOV video under 30 MB.")

class ListingForm(Styled, forms.ModelForm):
    no_prefill = ("house_type",)
    more = ("owner_email", "estate", "deposit", "units_total", "environment", "nearby_institutions", "nearby_hospitals", "nearby_shops",
            "nearby_transport", "nearby_landmarks", "around1", "video1")
    photo1 = forms.ImageField(required=False, label="Photo 1")
    photo2 = forms.ImageField(required=False, label="Photo 2")
    around1 = forms.ImageField(required=False, label="Photo of the surroundings (street, walkway)")
    video1 = forms.FileField(required=False, label="Short video of the house (optional)", validators=[_video_ok])
    class Meta:
        model = Property
        fields = ["owner_name", "owner_phone", "owner_email", "title", "area", "estate", "house_type", "rent", "deposit",
                  "units_total", "units_vacant", "description", "environment",
                  "nearby_institutions", "nearby_hospitals", "nearby_shops", "nearby_transport", "nearby_landmarks"] + [a for a, _ in AMENITIES]

class ProviderForm(Styled, forms.ModelForm):
    more = ("email", "package", "speed", "price", "install_fee", "details")
    class Meta:
        model = ServiceProvider
        fields = ["name", "business", "category", "phone", "email", "coverage", "package", "speed", "price", "install_fee", "details"]
