"""REST API for the future Android/iOS apps.  /api/properties/  /api/institutions/  POST /api/leads/"""
from django.db.models import F
from django.urls import include, path
from rest_framework import generics, routers, serializers, viewsets
from rest_framework.throttling import ScopedRateThrottle
from .models import Distance, Institution, Lead, Property, PropertyMedia

class MediaS(serializers.ModelSerializer):
    class Meta: model = PropertyMedia; fields = ["kind", "section", "file", "thumb"]
class DistS(serializers.ModelSerializer):
    institution = serializers.StringRelatedField()
    class Meta: model = Distance; fields = ["institution", "km"]
class PropertyS(serializers.ModelSerializer):
    media = MediaS(many=True, read_only=True)
    distances = DistS(many=True, read_only=True)
    amenities = serializers.ListField(source="amenity_list", read_only=True)
    verified = serializers.BooleanField(source="is_verified", read_only=True)
    class Meta:
        model = Property
        fields = ["slug", "title", "area", "estate", "house_type", "rent", "deposit", "description", "environment",
                  "amenities", "verification", "verified", "verified_on", "units_vacant", "media", "distances"]
class InstS(serializers.ModelSerializer):
    class Meta: model = Institution; fields = ["name", "slug"]
class LeadS(serializers.ModelSerializer):
    class Meta:
        model = Lead; fields = ["id", "kind", "name", "phone", "details", "property", "status"]
        read_only_fields = ["id", "status"]

class PropertyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class, lookup_field = PropertyS, "slug"
    def get_queryset(self):
        g = self.request.query_params
        qs = Property.objects.filter(status="approved", is_available=True).prefetch_related("media", "distances__institution")
        if g.get("type"): qs = qs.filter(house_type=g["type"])
        if g.get("max_rent", "").isdigit(): qs = qs.filter(rent__lte=int(g["max_rent"]))
        if g.get("near"): qs = qs.filter(distances__institution__slug=g["near"]).annotate(km=F("distances__km")).order_by("km")
        return qs

class LeadCreate(generics.CreateAPIView):
    serializer_class = LeadS
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "leads"

router = routers.DefaultRouter()
router.register("properties", PropertyViewSet, basename="api-property")
urlpatterns = [
    path("", include(router.urls)),
    path("institutions/", generics.ListAPIView.as_view(queryset=Institution.objects.all(), serializer_class=InstS, pagination_class=None)),
    path("leads/", LeadCreate.as_view()),
]
