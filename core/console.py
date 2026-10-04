from datetime import date, timedelta
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import PostForm
from .models import Area, SERVICE_CHOICES, Post, Review, Announcement, Lead, Property, SearchLog, ServiceProvider, _safe_link

PROP_ACTIONS = {"approve": dict(status="approved"), "reject": dict(status="rejected"), "verify": dict(verification="verified", verified_on=date.today()),
                "unverify": dict(verification="landlord"), "feature": dict(featured=True), "unfeature": dict(featured=False),
                "available": dict(is_available=True), "unavailable": dict(is_available=False)}
PROV_ACTIONS = {"approve": "approved", "suspend": "suspended"}

def staff(view):
    @wraps(view)
    def inner(request, *a, **k):
        if not (request.user.is_authenticated and request.user.is_staff): return redirect("console_login")
        return view(request, *a, **k)
    return inner

def _ctx(active, **extra):
    nl, npr, nv = (Lead.objects.filter(status="new").count(), Property.objects.filter(status="pending").count(),
                   ServiceProvider.objects.filter(status="pending").count())
    return {"active": active, "nav": [("home", "console", "Overview", 0, "grid"), ("leads", "console_leads", "Leads", nl, "inbox"),
            ("props", "console_props", "Houses", npr, "home"), ("areas", "console_areas", "Areas", 0, "pin"), ("providers", "console_providers", "Partners", nv, "store"),
            ("reviews", "console_reviews", "Reviews", Review.objects.filter(status="pending").count(), "star"),
            ("blog", "console_blog", "Blog", 0, "news"),
            ("announcements", "console_announcements", "Announcements", 0, "mega")], **extra}

def _back(request, default):
    nxt = request.POST.get("next", "")
    return redirect(nxt if nxt and url_has_allowed_host_and_scheme(nxt, request.get_host()) else default)

def login_view(request):
    if request.user.is_authenticated and request.user.is_staff: return redirect("console")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0].strip()
        key = f"login:{ip}"; cache.add(key, 0, 600)
        try: tries = cache.incr(key)
        except ValueError: tries = 1
        if tries > 8: form.add_error(None, "Too many attempts. Please wait 10 minutes and try again.")
        elif form.is_valid():
            if form.get_user().is_staff:
                login(request, form.get_user()); cache.delete(key); return redirect("console")
            form.add_error(None, "This account does not have staff access.")
    return render(request, "core/console/login.html", {"form": form})

def logout_view(request):
    logout(request); return redirect("console_login")

@staff
def home(request):
    P, L = Property.objects, Lead.objects
    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    counts = [L.filter(created_at__date=d).count() for d in days]
    top = max(counts) or 1
    by_status = {r["status"]: r["n"] for r in L.values("status").annotate(n=Count("id"))}
    total = sum(by_status.values()) or 1
    ctx = _ctx("home",
        cards=[("New leads", L.filter(status="new").count(), "text-coral", "console_leads"), ("Listings to review", P.filter(status="pending").count(), "text-coral", "console_props"),
               ("Partners to review", ServiceProvider.objects.filter(status="pending").count(), "text-coral", "console_providers"),
               ("Active listings", P.filter(status="approved", is_available=True).count(), "text-brand", "console_props"),
               ("Verified houses", P.filter(verification="verified").count(), "text-brand", "console_props"),
               ("Landlords", P.values("owner_phone").distinct().count(), "text-brand", "console_props"),
               ("Partners", ServiceProvider.objects.filter(status="approved").count(), "text-brand", "console_providers"),
               ("All leads", L.count(), "text-brand", "console_leads")],
        chart=[{"day": d.strftime("%a"), "n": n, "h": max(4, round(n / top * 100)) if n else 3} for d, n in zip(days, counts)],
        week=sum(counts),
        statuses=[{"label": lbl, "n": by_status.get(k, 0), "pct": round(by_status.get(k, 0) / total * 100)} for k, lbl in Lead.STATUS],
        recent=L.select_related("property")[:6], searched=SearchLog.objects.values("term").annotate(n=Count("id")).order_by("-n")[:6],
        viewed=P.filter(status="approved").order_by("-views")[:5])
    return render(request, "core/console/home.html", ctx)

def _client_wa(phone):
    d = "".join(c for c in phone if c.isdigit())
    if d.startswith("0"): d = "254" + d[1:]
    return f"https://wa.me/{d}"

@staff
def leads(request):
    qs = Lead.objects.select_related("property")
    st, kd = request.GET.get("status", ""), request.GET.get("kind", "")
    if st: qs = qs.filter(status=st)
    if kd: qs = qs.filter(kind=kd)
    rows = list(qs[:100])
    for l in rows: l.client_wa = _client_wa(l.phone)
    counts = {r["status"]: r["n"] for r in Lead.objects.values("status").annotate(n=Count("id"))}
    return render(request, "core/console/leads.html", _ctx("leads", rows=rows, st=st, kd=kd, kinds=Lead.KINDS, status_list=Lead.STATUS,
                  tabs=[("", "All", sum(counts.values()))] + [(k, lbl, counts.get(k, 0)) for k, lbl in Lead.STATUS]))

@staff
@require_POST
def lead_update(request, pk):
    l = get_object_or_404(Lead, pk=pk)
    if request.POST.get("status") in dict(Lead.STATUS): l.status = request.POST["status"]
    l.notes = request.POST.get("notes", l.notes)[:1000]; l.save()
    messages.success(request, f"Lead #{l.pk} updated.")
    return _back(request, "console_leads")

@staff
def props(request):
    st = request.GET.get("status", "pending")
    qs = Property.objects.all()
    if st in dict(Property.STATUS): qs = qs.filter(status=st)
    counts = {r["status"]: r["n"] for r in Property.objects.values("status").annotate(n=Count("id"))}
    return render(request, "core/console/props.html", _ctx("props", rows=qs[:100], st=st,
                  tabs=[(k, lbl, counts.get(k, 0)) for k, lbl in Property.STATUS] + [("all", "All", sum(counts.values()))]))

@staff
@require_POST
def prop_action(request, pk):
    act = request.POST.get("action")
    if act in PROP_ACTIONS:
        Property.objects.filter(pk=pk).update(**PROP_ACTIONS[act]); messages.success(request, f"Done: {act}.")
    return _back(request, "console_props")

@staff
def providers(request):
    st = request.GET.get("status", "")
    qs = ServiceProvider.objects.all()
    if st: qs = qs.filter(status=st)
    return render(request, "core/console/providers.html", _ctx("providers", rows=qs[:100], st=st))

@staff
@require_POST
def provider_action(request, pk):
    act = request.POST.get("action")
    if act in PROV_ACTIONS:
        ServiceProvider.objects.filter(pk=pk).update(status=PROV_ACTIONS[act]); messages.success(request, f"Partner {PROV_ACTIONS[act]}.")
    return _back(request, "console_providers")


def _date(v):
    try: return date.fromisoformat((v or "").strip())
    except ValueError: return None

def _num(v):
    try: return max(0, min(int(v), 9999))
    except (TypeError, ValueError): return 0

@staff
def announcements(request):
    if request.method == "POST":
        text = request.POST.get("text", "").strip()[:140]
        if text:
            Announcement.objects.create(text=text, link=_safe_link(request.POST.get("link")), expires_on=_date(request.POST.get("expires_on")), order=_num(request.POST.get("order")))
            messages.success(request, "Announcement added. It is now live on the homepage.")
        return redirect("console_announcements")
    return render(request, "core/console/announcements.html", _ctx("announcements", rows=Announcement.objects.all(), today=timezone.localdate()))

@staff
@require_POST
def announcement_action(request, pk):
    a = get_object_or_404(Announcement, pk=pk); act = request.POST.get("action")
    if act == "delete": a.delete(); messages.success(request, "Announcement deleted.")
    elif act == "toggle": a.is_active = not a.is_active; a.save(); messages.success(request, "Now live." if a.is_active else "Hidden from the website.")
    elif act == "save":
        text = request.POST.get("text", "").strip()[:140]
        if text: a.text = text
        a.link = _safe_link(request.POST.get("link")); a.expires_on = _date(request.POST.get("expires_on")); a.order = _num(request.POST.get("order")); a.save()
        messages.success(request, "Announcement saved.")
    return redirect("console_announcements")


REVIEW_ACTIONS = {"approve": dict(status="approved"), "reject": dict(status="rejected"), "feature": dict(featured=True), "unfeature": dict(featured=False)}

@staff
def reviews(request):
    if request.method == "POST":      # add a testimonial yourself (e.g. one a client sent on WhatsApp)
        p = request.POST; name, text = p.get("name", "").strip()[:60], p.get("text", "").strip()[:500]
        try: rating = min(5, max(1, int(p.get("rating", 5))))
        except ValueError: rating = 5
        if name and text:
            Review.objects.create(name=name, role=p.get("role", "").strip()[:80], service=p.get("service") if p.get("service") in dict(SERVICE_CHOICES) else "other",
                                  rating=rating, text=text, status="approved"); messages.success(request, "Review added and published.")
        return redirect("console_reviews")
    st = request.GET.get("status", "pending"); qs = Review.objects.all()
    if st in dict(Review.STATUS): qs = qs.filter(status=st)
    counts = {r["status"]: r["n"] for r in Review.objects.values("status").annotate(n=Count("id"))}
    return render(request, "core/console/reviews.html", _ctx("reviews", rows=qs[:100], st=st, services=SERVICE_CHOICES,
                  tabs=[(k, l, counts.get(k, 0)) for k, l in Review.STATUS] + [("all", "All", sum(counts.values()))]))

@staff
@require_POST
def review_action(request, pk):
    act = request.POST.get("action")
    if act == "delete": Review.objects.filter(pk=pk).delete(); messages.success(request, "Review deleted.")
    elif act in REVIEW_ACTIONS: Review.objects.filter(pk=pk).update(**REVIEW_ACTIONS[act]); messages.success(request, "Done.")
    return _back(request, "console_reviews")

@staff
def blog(request):
    return render(request, "core/console/blog.html", _ctx("blog", rows=Post.objects.all()))

@staff
def blog_edit(request, pk=None):
    post = get_object_or_404(Post, pk=pk) if pk else None
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Post saved."); return redirect("console_blog")
    return render(request, "core/console/blog_form.html", _ctx("blog", form=form, post=post))

@staff
@require_POST
def blog_action(request, pk):
    p = get_object_or_404(Post, pk=pk); act = request.POST.get("action")
    if act == "delete": p.delete(); messages.success(request, "Post deleted.")
    elif act == "toggle": p.is_published = not p.is_published; p.save(); messages.success(request, "Published." if p.is_published else "Moved back to drafts.")
    return redirect("console_blog")


def _clean_name(v): return " ".join((v or "").split())[:80]

@staff
def areas(request):
    if request.method == "POST":
        name = _clean_name(request.POST.get("name"))
        if not name: pass
        elif Area.objects.filter(name__iexact=name).exists(): messages.success(request, f"\u201c{name}\u201d is already in the list.")
        else: Area.objects.create(name=name, order=_num(request.POST.get("order"))); messages.success(request, f"\u201c{name}\u201d added. Visitors can now pick it in the house search.")
        return redirect("console_areas")
    rows = list(Area.objects.all()); live = Property.objects.filter(status="approved", is_available=True)
    for a in rows: a.houses = live.filter(Q(area__icontains=a.name) | Q(estate__icontains=a.name)).count()
    have = {a.name.lower() for a in rows}
    used = Property.objects.filter(status="approved").exclude(area="").values("area").annotate(n=Count("id")).order_by("-n")
    sug = [r for r in used if r["area"].strip().lower() not in have][:12]
    return render(request, "core/console/areas.html", _ctx("areas", rows=rows, suggestions=sug))

@staff
@require_POST
def area_action(request, pk):
    a = get_object_or_404(Area, pk=pk); act = request.POST.get("action")
    if act == "delete": a.delete(); messages.success(request, "Area removed from the search options.")
    elif act == "toggle": a.is_active = not a.is_active; a.save(); messages.success(request, "Now shown in the search." if a.is_active else "Hidden from the search.")
    elif act == "save":
        name = _clean_name(request.POST.get("name"))
        if name and not Area.objects.filter(name__iexact=name).exclude(pk=a.pk).exists(): a.name = name
        a.order = _num(request.POST.get("order")); a.save(); messages.success(request, "Area saved.")
    return redirect("console_areas")