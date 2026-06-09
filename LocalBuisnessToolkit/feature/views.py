from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Appointment, Customer, Invoice, Notification


# ========== PUBLIC VIEWS (Anyone can view) ==========

def home(request):
    """Public home page"""
    return render(request, 'feature/home.html')


def about(request):
    """Public about page"""
    return render(request, 'feature/about.html')


def pricing(request):
    """Public pricing page"""
    return render(request, 'feature/pricing.html')


def contact(request):
    """Public contact page"""
    return render(request, 'feature/contact.html')


def dashboard(request):
    """
    Anyone can VIEW the dashboard, but with limited/sample data
    or showing a preview/message that they need to login
    """
    if request.user.is_authenticated:
        # Logged in users see their real data
        customers = Customer.objects.filter(owner=request.user)
        appointments = Appointment.objects.filter(customer__owner=request.user)
        invoices = Invoice.objects.filter(customer__owner=request.user)
        notifications = Notification.objects.filter(owner=request.user)
        
        context = {
            "message": f"Welcome {request.user.username}",
            "appointments_count": appointments.count(),
            "customers_count": customers.count(),
            "invoices_unpaid": invoices.filter(status="unpaid").count(),
            "notifications_count": notifications.count(),
            "recent_appointments": appointments.order_by("-date")[:5],
            "recent_invoices": invoices.order_by("-created_at")[:5],
            "user_logged_in": True,
        }
    else:
        # Non-logged in users see a demo/preview
        context = {
            "message": "Sign in to manage your appointments, customers, and invoices",
            "appointments_count": "?",
            "customers_count": "?",
            "invoices_unpaid": "?",
            "notifications_count": "?",
            "recent_appointments": [],
            "recent_invoices": [],
            "user_logged_in": False,
            "login_required": True,
        }
    return render(request, "feature/dashboard.html", context)


def appointment(request):
    """
    Anyone can VIEW the appointments list, but to interact (create/edit/delete)
    they need to login
    """
    if request.user.is_authenticated:
        appointments = Appointment.objects.filter(customer__owner=request.user).order_by('-date')
        now = timezone.now()
        context = {
            "appointments": appointments,
            "appointments_count": appointments.count(),
            "upcoming_appointments": appointments.filter(date__gte=now).count(),
            "past_appointments": appointments.filter(date__lt=now).count(),
            "user_logged_in": True,
        }
    else:
        # Non-logged in users see a preview/empty state with login prompt
        context = {
            "appointments": [],
            "appointments_count": 0,
            "upcoming_appointments": 0,
            "past_appointments": 0,
            "user_logged_in": False,
            "login_required": True,
        }
    return render(request, "feature/appointments.html", context)


def customers(request):
    """Anyone can VIEW customers list, but to manage need login"""
    if request.user.is_authenticated:
        customers = Customer.objects.filter(owner=request.user)
        context = {
            "customers": customers,
            "customers_count": customers.count(),
            "user_logged_in": True,
        }
    else:
        context = {
            "customers": [],
            "customers_count": 0,
            "user_logged_in": False,
            "login_required": True,
        }
    return render(request, "feature/customers.html", context)


def invoices(request):
    """Anyone can VIEW invoices list, but to manage need login"""
    if request.user.is_authenticated:
        invoices = Invoice.objects.filter(customer__owner=request.user)
        context = {
            "invoices": invoices,
            "invoices_count": invoices.count(),
            "invoices_unpaid": invoices.filter(status="unpaid").count(),
            "invoices_paid": invoices.filter(status="paid").count(),
            "user_logged_in": True,
        }
    else:
        context = {
            "invoices": [],
            "invoices_count": 0,
            "invoices_unpaid": 0,
            "invoices_paid": 0,
            "user_logged_in": False,
            "login_required": True,
        }
    return render(request, "feature/invoices.html", context)


def notifications(request):
    """Anyone can VIEW notifications, but to manage need login"""
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(owner=request.user).order_by('-created_at')
        context = {
            "notifications": notifications,
            "notifications_count": notifications.count(),
            "unread_count": notifications.filter(is_read=False).count(),
            "user_logged_in": True,
        }
    else:
        context = {
            "notifications": [],
            "notifications_count": 0,
            "unread_count": 0,
            "user_logged_in": False,
            "login_required": True,
        }
    return render(request, "feature/notifications.html", context)


# ========== PROTECTED VIEWS (Require Login for Actions) ==========

@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, customer__owner=request.user)
    context = {
        "appointment": appointment,
    }
    return render(request, "feature/appointment_detail.html", context)


@login_required
def appointment_create(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        notes = request.POST.get('notes')
        
        appointment_datetime = None
        if date_str and time_str:
            appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())

        appointment = Appointment.objects.create(
            customer_id=customer_id,
            date=appointment_datetime,
            notes=notes,
        )
        
        messages.success(request, 'Appointment created successfully!')
        return redirect('feature:appointment_detail', appointment_id=appointment.id)
    
    customers = Customer.objects.filter(owner=request.user)
    context = {
        "customers": customers,
    }
    return render(request, "feature/appointment_form.html", context)


@login_required
def appointment_edit(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, customer__owner=request.user)
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        notes = request.POST.get('notes')

        if date_str and time_str:
            appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
            appointment.date = appointment_datetime

        appointment.notes = notes
        appointment.save()
        
        messages.success(request, 'Appointment updated successfully!')
        return redirect('feature:appointment_detail', appointment_id=appointment.id)
    
    context = {
        "appointment": appointment,
        "customers": Customer.objects.filter(owner=request.user),
    }
    return render(request, "feature/appointment_form.html", context)


@login_required
def appointment_delete(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, customer__owner=request.user)
    
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, 'Appointment deleted successfully!')
        return redirect('feature:appointments')
    
    context = {
        "appointment": appointment,
    }
    return render(request, "feature/appointment_confirm_delete.html", context)


@login_required
def settings(request):
    user = request.user
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('feature:settings')
    
    context = {
        "user": user,
    }
    return render(request, "feature/settings.html", context)