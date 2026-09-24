from django.conf import settings
from .utils import wa_link
def site(request):
    return {"PHONE": settings.PHONE, "EMAIL": settings.EMAIL, "WA": wa_link("Hello AMOX Homes, I need help."),
            "WA_PACKAGE": wa_link("Hello AMOX Homes, I want the Move-In Package (house search, moving, mattress, gas, internet)."),
            "WA_LANDLORD": wa_link("Hello AMOX Homes, I am a landlord and want to ask about Pro listing / verification.")}
