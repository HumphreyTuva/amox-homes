from django.urls import path
from . import views as v
urlpatterns = [
    path("", v.home, name="home"),
    path("houses/", v.property_list, name="houses"),
    path("houses/near/<slug:institution>/", v.property_list, name="houses_near"),
    path("houses/<slug:slug>/", v.property_detail, name="property_detail"),
    path("services/", v.services, name="services"),
    path("request/<slug:kind>/", v.request_service, name="request"),
    path("landlords/", v.landlords, name="landlords"),
    path("landlords/list/", v.list_property, name="list_property"),
    path("providers/", v.providers, name="providers"),
    path("about/", v.about, name="about"),
    path("contact/", v.contact, name="contact"),
    path("thanks/", v.thanks, name="thanks"),
    path("privacy/", v.legal, {"page": "privacy"}, name="privacy"),
    path("terms/", v.legal, {"page": "terms"}, name="terms"),
    path("dashboard/", v.dashboard, name="dashboard"),
]
