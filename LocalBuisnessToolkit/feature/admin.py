from django.contrib import admin
from .models import Customer, Appointment, Invoice, Notification

# Customize how each model appears in the admin list view
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at")
    search_fields = ("name", "email")

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("customer", "date", "notes")
    search_fields = ("customer__name",)
    list_filter = ("date",)

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("customer", "amount", "status", "created_at")
    search_fields = ("customer__name",)
    list_filter = ("status",)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ("message", "created_at", "is_read")
    list_filter = ("is_read",)

# Register models with their admin classes
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Notification, NotificationAdmin)
