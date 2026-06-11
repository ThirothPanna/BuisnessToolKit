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
    owner_lookup = "user"  # Changed to match your model's field name
    list_display = ("title", "message", "user", "notification_type", "priority", "created_at", "is_read")
    list_filter = ("is_read", "notification_type", "priority")
    search_fields = ("title", "message", "user__username", "user__email")
    readonly_fields = ("created_at",)
    
    def get_exclude(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_exclude(request, obj)
        return ("user",)  # Hide the user field for non-superusers
    
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.user = request.user  # Auto-assign the current user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Show users only their own notifications"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


# Register models with their admin classes
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Notification, NotificationAdmin)