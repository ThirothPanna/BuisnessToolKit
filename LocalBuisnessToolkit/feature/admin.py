from django.contrib import admin
from .models import Customer, Appointment, Invoice, Notification


class OwnerScopedAdmin(admin.ModelAdmin):
    owner_lookup = "owner"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(**{self.owner_lookup: request.user})


# Customize how each model appears in the admin list view
class CustomerAdmin(OwnerScopedAdmin):
    list_display = ("name", "email", "phone", "owner", "created_at")
    search_fields = ("name", "email")

    def get_exclude(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_exclude(request, obj)
        return ("owner",)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


class AppointmentAdmin(OwnerScopedAdmin):
    owner_lookup = "customer__owner"
    list_display = ("customer", "date", "notes")
    search_fields = ("customer__name",)
    list_filter = ("date",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "customer" and not request.user.is_superuser:
            kwargs["queryset"] = Customer.objects.filter(owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class InvoiceAdmin(OwnerScopedAdmin):
    owner_lookup = "customer__owner"
    list_display = ("customer", "amount", "status", "created_at")
    search_fields = ("customer__name",)
    list_filter = ("status",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "customer" and not request.user.is_superuser:
            kwargs["queryset"] = Customer.objects.filter(owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class NotificationAdmin(OwnerScopedAdmin):
    list_display = ("message", "owner", "created_at", "is_read")
    list_filter = ("is_read",)

    def get_exclude(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_exclude(request, obj)
        return ("owner",)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


# Register models with their admin classes
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Notification, NotificationAdmin)
