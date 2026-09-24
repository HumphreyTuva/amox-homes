from django.core.management.base import BaseCommand
from core.models import Distance, Institution, Property

class Command(BaseCommand):
    help = "Create demo institutions and sample listings"
    def handle(self, *a, **k):
        inst = {n: Institution.objects.get_or_create(slug=s, defaults={"name": n})[0] for n, s in [
            ("MKU Malindi", "mku-malindi"), ("KMTC Malindi", "kmtc-malindi"), ("Pwani University", "pwani-university"),
            ("Malindi Sub-County Hospital", "malindi-sub-county-hospital")]}
        rows = [("Modern Bedsitter", "Malindi Town", "Bedsitter", 7000, dict(wifi=True, water=True, security=True), [1.5, 3.2, 25, 2]),
                ("Student Single Room", "Shella", "Single room", 4500, dict(water=True), [0.8, 2.5, 26, 3]),
                ("Furnished Studio", "Lamu Road", "Studio", 15000, dict(wifi=True, furnished=True, security=True), [3, 1, 25, 2.5]),
                ("One Bedroom with Balcony", "Section 9", "One bedroom", 12000, dict(balcony=True, parking=True, cctv=True), [4, 2, 24, 1.5])]
        for t, area, ty, rent, am, d in rows:
            p, made = Property.objects.get_or_create(title=t, area=area, defaults=dict(
                owner_name="Demo Landlord", owner_phone="0700000000", house_type=ty, rent=rent, deposit=rent, status="approved",
                verification="verified", description="Sample listing. Replace with real details.", environment="Shops and transport nearby.", **am))
            if made:
                for i, km in zip(inst.values(), d): Distance.objects.create(property=p, institution=i, km=km)
        self.stdout.write("Demo data ready. Photos can be added in the admin.")
