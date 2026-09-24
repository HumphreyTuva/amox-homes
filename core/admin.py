from datetime import date
from django.contrib import admin
from .models import Institution, Property, PropertyMedia, Distance, Lead, ServiceProvider, SearchLog

class MediaInline(admin.TabularInline): model = PropertyMedia; extra = 1
class DistInline(admin.TabularInline): model = Distance; extra = 1

@admin.register(Institution)
class InstAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "area", "house_type", "rent", "status", "verification", "is_available", "featured", "views")
    list_filter = ("status", "verification", "is_available", "featured", "house_type", "area")
    search_fields = ("title", "area", "estate", "owner_name", "owner_phone")
    inlines = [MediaInline, DistInline]
    actions = ["approve", "reject", "verify", "feature", "unfeature", "available", "unavailable"]

    @admin.action(description="Approve listings")
    def approve(self, r, qs): qs.update(status="approved")
    @admin.action(description="Reject listings")
    def reject(self, r, qs): qs.update(status="rejected")
    @admin.action(description="Mark AMOX Verified")
    def verify(self, r, qs): qs.update(verification="verified", verified_on=date.today())
    @admin.action(description="Feature on top page")
    def feature(self, r, qs): qs.update(featured=True)
    @admin.action(description="Remove from featured")
    def unfeature(self, r, qs): qs.update(featured=False)
    @admin.action(description="Mark available")
    def available(self, r, qs): qs.update(is_available=True)
    @admin.action(description="Mark unavailable")
    def unavailable(self, r, qs): qs.update(is_available=False)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "name", "phone", "property", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("kind", "status")
    search_fields = ("name", "phone")
    readonly_fields = ("created_at",)

@admin.register(ServiceProvider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("business", "category", "package", "price", "coverage", "commission_pct", "status")
    list_filter = ("category", "status")
    actions = ["approve", "suspend"]
    @admin.action(description="Approve providers")
    def approve(self, r, qs): qs.update(status="approved")
    @admin.action(description="Suspend providers")
    def suspend(self, r, qs): qs.update(status="suspended")

@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ("term", "created_at")
    search_fields = ("term",)
