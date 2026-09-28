from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from core.sitemaps import SITEMAPS

admin.site.site_header = "AMOXHomes Admin"
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.api")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}),
    path("", include("core.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
