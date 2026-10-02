from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Institution, Post, Property

class Static(Sitemap):
    def items(self): return ["home", "houses", "services", "landlords", "providers", "about", "contact", "blog", "reviews"]
    def location(self, n): return reverse(n)
class Props(Sitemap):
    def items(self): return Property.objects.filter(status="approved")
    def lastmod(self, o): return o.updated_at
class Insts(Sitemap):
    def items(self): return Institution.objects.all()
    def location(self, o): return reverse("houses_near", args=[o.slug])
class Posts(Sitemap):
    def items(self): return Post.live()
    def lastmod(self, o): return o.updated_at
SITEMAPS = {"static": Static, "houses": Props, "institutions": Insts, "blog": Posts}
