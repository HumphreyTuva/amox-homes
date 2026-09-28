from django.conf import settings
from .utils import wa_link
def site(request):
    return {"PHONE": settings.PHONE, "EMAIL": settings.EMAIL, "WA": wa_link("Hello AMOXHomes, I would like to find a home and learn about your settling-in services. Could you assist me, please?"),
            "WA_PACKAGE": wa_link("Hello AMOXHomes, I want the Move-In Package (house search, moving, mattress, gas, internet)."),
            "WA_LANDLORD": wa_link("Hello AMOXHomes, I am a landlord and want to ask about Pro listing / verification.")}
