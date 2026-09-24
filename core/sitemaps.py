from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Institution, Property

class Static(Sitemap):
    def items(self): return ["home", "houses", "services", "landlords", "providers", "about", "contact"]
    def location(self, n): return reverse(n)
class Props(Sitemap):
    def items(self): return Property.objects.filter(status="approved")
    def lastmod(self, o): return o.updated_at
class Insts(Sitemap):
    def items(self): return Institution.objects.all()
    def location(self, o): return reverse("houses_near", args=[o.slug])
SITEMAPS = {"static": Static, "houses": Props, "institutions": Insts}
