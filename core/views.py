from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from .utils import wa_link, notify
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import *
from .models import AMENITIES, HOUSE_TYPES, Institution, Lead, Property, PropertyMedia, SearchLog, ServiceProvider

def _guard(request):
    """Honeypot + simple per-IP limit for public forms."""
    if request.POST.get("website"): return redirect("home")
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0].strip()
    key = f"posts:{ip}"; cache.add(key, 0, 3600)
    try: n = cache.incr(key)
    except ValueError: n = 1
    if n > 12: return HttpResponse("Too many requests. Please try again later.", status=429)

def live():
    return Property.objects.filter(status="approved", is_available=True).prefetch_related("media")

def _int(v):
    try: return int(v)
    except (TypeError, ValueError): return None

def home(request):
    return render(request, "core/home.html", {"featured": live().order_by("-featured", "-verification", "-created_at")[:6],
                                              "institutions": Institution.objects.all(), "services": list(SERVICES.items())})

def property_list(request, institution=None):
    g, qs = request.GET, live()
    near = g.get("near")
    if near is not None and near != (institution or ""):
        rest = g.copy(); rest.pop("near", None); rest.pop("page", None)
        return redirect((reverse("houses_near", args=[near]) if near else reverse("houses")) + (f"?{rest.urlencode()}" if rest else ""))
    inst = get_object_or_404(Institution, slug=institution) if institution else None
    term = (g.get("q") or (inst.name if inst else "")).strip().lower()[:80]
    if term and not g.get("page"): SearchLog.objects.create(term=term)
    if g.get("q"): qs = qs.filter(Q(title__icontains=g["q"]) | Q(area__icontains=g["q"]) | Q(estate__icontains=g["q"]))
    if g.get("type"): qs = qs.filter(house_type=g["type"])
    if _int(g.get("min")) is not None: qs = qs.filter(rent__gte=_int(g["min"]))
    if _int(g.get("max")) is not None: qs = qs.filter(rent__lte=_int(g["max"]))
    for a, _ in AMENITIES:
        if g.get(a): qs = qs.filter(**{a: True})
    if g.get("verified"): qs = qs.filter(verification="verified")
    sort = {"price_asc": "rent", "price_desc": "-rent", "new": "-created_at"}.get(g.get("sort"))
    if sort: qs = qs.order_by(sort)
    if inst:
        qs = qs.filter(distances__institution=inst).annotate(km=F("distances__km")).order_by("km")
    page = Paginator(qs, 12).get_page(g.get("page"))
    params = g.copy(); params.pop("page", None)
    return render(request, "core/list.html", {"page": page, "inst": inst, "types": HOUSE_TYPES, "amenities": AMENITIES,
                                              "qs": params.urlencode(), "g": g, "institutions": Institution.objects.all(), "total": page.paginator.count})

def property_detail(request, slug):
    p = get_object_or_404(Property, slug=slug, status="approved")
    Property.objects.filter(pk=p.pk).update(views=F("views") + 1)
    media = list(p.media.all())
    form = InquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        return _save_lead(request, "inquiry", form, p)
    return render(request, "core/detail.html", {
        "p": p, "form": form, "distances": p.distances.select_related("institution"),
        "inside": [m for m in media if m.section == "inside" and m.kind == "photo"],
        "around": [m for m in media if m.section == "around" and m.kind == "photo"],
        "videos": [m for m in media if m.kind == "video"],
        "p_wa": wa_link(f"Hi AMOX Homes, I'm interested in {p.title} in {p.area}: {request.build_absolute_uri()}"),
        "share": f"{p.title} in {p.area}, KSh {int(p.rent):,}/month: {request.build_absolute_uri()}",
        "report_wa": wa_link(f"Hi AMOX Homes, I want to report this listing: {request.build_absolute_uri()}")})

def legal(request, page):
    return render(request, "core/legal.html", {"page": page})

def thanks(request):
    kind, pk = request.session.get("last", [None, None])
    ctx = {}
    if kind == "lead": ctx["lead"] = Lead.objects.filter(pk=pk).first()
    elif kind == "listed": ctx["listed"] = Property.objects.filter(pk=pk).first()
    elif kind == "provider": ctx["provider"] = True
    if not any(ctx.values()): return redirect("home")
    return render(request, "core/thanks.html", ctx)

def _save_lead(request, kind, form, prop=None):
    if (blocked := _guard(request)): return blocked
    cd = form.cleaned_data
    details = {k.replace("_", " ").capitalize(): str(v) for k, v in cd.items() if k not in ("name", "phone") and v}
    lead = Lead.objects.create(kind=kind, name=cd["name"], phone=cd["phone"], details=details, property=prop)
    notify(f"New {lead.get_kind_display()} #{lead.pk}", lead.wa_text())
    request.session["last"] = ["lead", lead.pk]
    return redirect("thanks")

def request_service(request, kind):
    if kind not in SERVICES: return redirect("services")
    title, intro, icon, Form = SERVICES[kind]
    form = Form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        return _save_lead(request, kind, form)
    return render(request, "core/form_page.html", {"title": title, "intro": intro, "form": form, "btn": "Send request",
                                                  "partners": ServiceProvider.objects.filter(category=kind, status="approved")})

def services(request): return render(request, "core/services.html", {"services": list(SERVICES.items())})

def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid(): return _save_lead(request, "general", form)
    return render(request, "core/form_page.html", {"title": "Contact us", "intro": "We reply fastest on WhatsApp. You can also use this form to report a listing.", "form": form, "btn": "Send enquiry", "contact": True})

def landlords(request):
    return render(request, "core/landlords.html")

def list_property(request):
    form = ListingForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        if (blocked := _guard(request)): return blocked
        p = form.save(commit=False); p.status = "pending"; p.verification = "landlord"; p.save()
        for key, sec in (("photo1", "inside"), ("photo2", "inside"), ("around1", "around")):
            if form.cleaned_data.get(key): PropertyMedia.objects.create(property=p, file=form.cleaned_data[key], section=sec)
        if form.cleaned_data.get("video1"): PropertyMedia.objects.create(property=p, kind="video", section="around", file=form.cleaned_data["video1"])
        notify(f"New listing: {p.title}", f"{p.area}, KSh {p.rent}\n{p.owner_name} {p.owner_phone}\nReview it in the admin.")
        request.session["last"] = ["listed", p.pk]
        return redirect("thanks")
    return render(request, "core/form_page.html", {"title": "List your property", "intro": "Basic listings are free and include 2 photos. We review every listing before it goes live. Ask us about Pro listing and verification.", "form": form, "btn": "Submit listing"})

def providers(request):
    form = ProviderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if (blocked := _guard(request)): return blocked
        pv = form.save(); notify(f"New provider: {pv.business}", f"{pv.get_category_display()}, {pv.phone}\nApprove it in the admin.")
        request.session["last"] = ["provider", pv.pk]
        return redirect("thanks")
    return render(request, "core/form_page.html", {"title": "Register as a service provider", "intro": "Tenants request a connection through AMOX Homes and we refer them to approved partners.", "form": form, "btn": "Register my business"})

def about(request): return render(request, "core/about.html")

@staff_member_required
def dashboard(request):
    L = Lead.objects
    ctx = {
        "stats": [("Landlords", Property.objects.values("owner_phone").distinct().count()), ("Properties", Property.objects.count()),
                  ("Active listings", live().count()), ("Pending review", Property.objects.filter(status="pending").count()),
                  ("Verified", Property.objects.filter(verification="verified").count()),
                  ("Providers", ServiceProvider.objects.filter(status="approved").count()),
                  ("House inquiries", L.filter(kind__in=["house", "inquiry"]).count()),
                  ("Successful connections", L.filter(status__in=["connected", "completed"]).count()),
                  ("New leads", L.filter(status="new").count())],
        "by_kind": [{"kind": dict(Lead.KINDS).get(r["kind"], r["kind"]), "n": r["n"]} for r in L.values("kind").annotate(n=Count("id")).order_by("-n")],
        "searched": SearchLog.objects.values("term").annotate(n=Count("id")).order_by("-n")[:8],
        "top_viewed": Property.objects.order_by("-views")[:8],
        "recent": L.select_related("property")[:10],
    }
    return render(request, "core/dashboard.html", ctx)
