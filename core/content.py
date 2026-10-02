from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Post, Review, SERVICE_CHOICES
from .utils import notify
from .views import _guard

def reviews(request):
    ctx = {"services": SERVICE_CHOICES}
    if request.method == "POST":
        if (blocked := _guard(request)): return blocked
        p = request.POST; name, text = p.get("name", "").strip(), p.get("text", "").strip()
        try: rating = int(p.get("rating", 0))
        except ValueError: rating = 0
        service = p.get("service", "")
        if 1 <= len(name) <= 60 and 10 <= len(text) <= 500 and 1 <= rating <= 5 and service in dict(SERVICE_CHOICES):
            r = Review.objects.create(name=name, role=p.get("role", "").strip()[:80], service=service, rating=rating, text=text)
            notify(f"New review ({rating}/5) from {name}", f"{text}\n\nApprove or reject it in the console.")
            return redirect(reverse("reviews") + "?sent=1#write")
        ctx.update(error=True, posted=p)
    qs = Review.objects.filter(status="approved"); agg = qs.aggregate(avg=Avg("rating"), n=Count("id"))
    ctx.update(rows=qs[:60], avg=round(agg["avg"], 1) if agg["avg"] else None, n=agg["n"], sent=request.GET.get("sent"))
    return render(request, "core/reviews.html", ctx)

def blog_list(request):
    cat = request.GET.get("c", ""); qs = Post.live()
    if cat in dict(Post.CATEGORIES): qs = qs.filter(category=cat)
    else: cat = ""
    return render(request, "core/blog_list.html", {"posts": qs[:60], "cat": cat, "cats": Post.CATEGORIES})

def blog_detail(request, slug):
    p = get_object_or_404(Post, slug=slug, is_published=True)
    return render(request, "core/blog_detail.html", {"p": p, "related": Post.live().exclude(pk=p.pk)[:3],
                  "share": f"{p.title}: {request.build_absolute_uri()}"})
