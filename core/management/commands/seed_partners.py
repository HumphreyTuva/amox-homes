from django.core.management.base import BaseCommand
from core.models import ServiceProvider

DEMO = [
    ("Sample Fibre (demo)", "internet", "Home Fibre", "10 Mbps", "KSh 2,500/month", "KSh 3,000", "Malindi Town, Shella", ""),
    ("Sample Hotspot (demo)", "internet", "Student Hotspot", "5 Mbps", "KSh 1,500/month", "Free", "Malindi, Kilifi", ""),
    ("Sample Gas (demo)", "gas", "6 kg cylinder hire", "", "KSh 300 per refill", "", "Malindi Town", "Delivery available."),
    ("Sample Home Essentials (demo)", "items", "Mattress hire", "", "KSh 500/month", "", "Malindi", "Beds, chairs, tables and curtains also available."),
    ("Sample Movers (demo)", "moving", "Pickup truck", "", "From KSh 3,000", "", "Malindi and Kilifi", ""),
]

class Command(BaseCommand):
    help = "Add clearly-labelled demo partners. Delete them in the admin before going live."
    def handle(self, *a, **k):
        for biz, cat, pkg, spd, price, fee, cov, det in DEMO:
            ServiceProvider.objects.get_or_create(business=biz, defaults=dict(name="Demo", category=cat, phone="0700000000", package=pkg, speed=spd,
                price=price, install_fee=fee, coverage=cov, details=det, status="approved"))
        self.stdout.write("Demo partners ready.")
