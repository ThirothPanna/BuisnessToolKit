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
    customers = Customer.objects.filter(owner=request.user)
    appointments = Appointment.objects.filter(customer__owner=request.user)
    invoices = Invoice.objects.filter(customer__owner=request.user)
    notifications = Notification.objects.filter(owner=request.user)

    context = {
        "message": f"Welcome {request.user.username}, you are a Business Owner!",
        "appointments_count": appointments.count(),
        "customers_count": customers.count(),
        "invoices_unpaid": invoices.filter(status="unpaid").count(),
        "notifications_count": notifications.count(),
        "recent_appointments": appointments.order_by("-date")[:5],
        "recent_invoices": invoices.order_by("-created_at")[:5],
    }
    return render(request, "dashboard.html", context)
