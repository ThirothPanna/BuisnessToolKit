from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Appointment, Customer, Invoice, Notification


def home(request):
    return render(request, 'feature/home.html')  # ✅ Fixed - added 'feature/'


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
    return render(request, "feature/dashboard.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
def appointment(request):
    appointments = Appointment.objects.filter(customer__owner=request.user).order_by('-date')
    
    now = timezone.now()
    context = {
        "appointments": appointments,
        "appointments_count": appointments.count(),
        "upcoming_appointments": appointments.filter(date__gte=now).count(),
        "past_appointments": appointments.filter(date__lt=now).count(),
    }
    return render(request, "feature/appointments.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, customer__owner=request.user)
    
    context = {
        "appointment": appointment,
    }
    return render(request, "feature/appointment_detail.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
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
    return render(request, "feature/appointment_form.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
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
    return render(request, "feature/appointment_form.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
def appointment_delete(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, customer__owner=request.user)
    
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, 'Appointment deleted successfully!')
        return redirect('feature:appointments')
    
    context = {
        "appointment": appointment,
    }
    return render(request, "feature/appointment_confirm_delete.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
def customers(request):
    customers = Customer.objects.filter(owner=request.user)
    
    context = {
        "customers": customers,
        "customers_count": customers.count(),
    }
    return render(request, "feature/customers.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
def invoices(request):
    invoices = Invoice.objects.filter(customer__owner=request.user)
    
    context = {
        "invoices": invoices,
        "invoices_count": invoices.count(),
        "invoices_unpaid": invoices.filter(status="unpaid").count(),
        "invoices_paid": invoices.filter(status="paid").count(),
    }
    return render(request, "feature/invoices.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
def notifications(request):
    notifications = Notification.objects.filter(owner=request.user).order_by('-created_at')
    
    context = {
        "notifications": notifications,
        "notifications_count": notifications.count(),
        "unread_count": notifications.filter(is_read=False).count(),
    }
    return render(request, "feature/notifications.html", context)  # ✅ Fixed


@login_required
@user_passes_test(is_business_owner)
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
    return render(request, "feature/settings.html", context)  # ✅ Fixed