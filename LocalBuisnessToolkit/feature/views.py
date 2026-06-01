from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import Appointment, Customer, Invoice, Notification

def home(request):
    return render(request, 'home.html')


def is_business_owner(user):
    return user.is_superuser or user.groups.filter(name="BusinessOwner").exists()


@login_required
@user_passes_test(is_business_owner)
def dashboard(request):
    context = {
        "message": f"Welcome {request.user.username}, you are a Business Owner!",
        "appointments_count": Appointment.objects.count(),
        "customers_count": Customer.objects.count(),
        "invoices_unpaid": Invoice.objects.filter(status="unpaid").count(),
        "notifications_count": Notification.objects.count(),
        "recent_appointments": Appointment.objects.order_by("-date")[:5],
        "recent_invoices": Invoice.objects.order_by("-created_at")[:5],
    }
    return render(request, "dashboard.html", context)
