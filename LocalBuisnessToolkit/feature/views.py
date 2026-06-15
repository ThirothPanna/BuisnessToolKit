from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
from .models import Appointment, Customer, Invoice, Notification
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .notification_utils import get_user_notifications, mark_all_as_read, get_unread_count


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
        notifications = Notification.objects.filter(user=request.user)
        
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


@login_required
def add_customer(request):
    """Add a new customer"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        if not name or not email:
            messages.error(request, 'Name and Email are required fields.')
            return redirect('feature:customers')
        
        # Check if customer with this email already exists for this user
        if Customer.objects.filter(owner=request.user, email=email).exists():
            messages.warning(request, f'A customer with email "{email}" already exists.')
            return redirect('feature:customers')
        
        # Create the new customer
        customer = Customer.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            owner=request.user
        )
        
        messages.success(request, f'Customer "{customer.name}" added successfully!')
        return redirect('feature:customers')
    
    # If not POST, redirect back to customers page
    return redirect('feature:customers')


def invoices(request):
    """Anyone can VIEW invoices list, but to manage need login"""
    if request.user.is_authenticated:
        invoices = Invoice.objects.filter(
            Q(customer__owner=request.user) | Q(user=request.user)
        ).distinct()
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
    customers = Customer.objects.filter(owner=request.user)
    
    if not customers.exists():
        messages.warning(request, 'You need to add a customer before creating an appointment.')
        return redirect('feature:customers')
    
    selected_customer_id = None
    date_value = None
    time_value = None
    notes_value = None

    if request.method == 'POST':
        selected_customer_id = request.POST.get('customer_id')
        date_value = request.POST.get('date')
        time_value = request.POST.get('time')
        notes_value = request.POST.get('notes')
        
        if not selected_customer_id or not date_value or not time_value:
            messages.error(request, 'Please provide customer, date, and time.')
            return render(request, "feature/appointment_form.html", {
                "customers": customers,
                "selected_customer_id": selected_customer_id,
                "date_value": date_value,
                "time_value": time_value,
                "notes": notes_value,
            })
        
        try:
            customer = Customer.objects.get(id=selected_customer_id, owner=request.user)
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid customer selected.')
            return render(request, "feature/appointment_form.html", {
                "customers": customers,
                "selected_customer_id": selected_customer_id,
                "date_value": date_value,
                "time_value": time_value,
                "notes": notes_value,
            })
        
        try:
            appointment_datetime = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
        except ValueError:
            messages.error(request, 'Invalid date or time format.')
            return render(request, "feature/appointment_form.html", {
                "customers": customers,
                "selected_customer_id": selected_customer_id,
                "date_value": date_value,
                "time_value": time_value,
                "notes": notes_value,
            })

        if appointment_datetime < timezone.now():
            messages.warning(request, 'You are creating an appointment in the past. Consider updating the date/time.')

        appointment = Appointment.objects.create(
            customer=customer,
            date=appointment_datetime,
            notes=notes_value,
            user=request.user,
        )
        
        messages.success(request, f'Appointment created successfully for {customer.name}!')
        return redirect('feature:appointment_detail', appointment_id=appointment.id)

    return render(request, "feature/appointment_form.html", {
        "customers": customers,
    })


@login_required
def appointment_edit(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, customer__owner=request.user)
    customers = Customer.objects.filter(owner=request.user)

    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        notes = request.POST.get('notes')
        
        selected_customer_id = customer_id or appointment.customer_id
        date_value = date_str
        time_value = time_str
        notes_value = notes

        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id, owner=request.user)
                appointment.customer = customer
            except Customer.DoesNotExist:
                messages.error(request, 'Invalid customer selected.')
                return render(request, "feature/appointment_form.html", {
                    "appointment": appointment,
                    "customers": customers,
                    "selected_customer_id": selected_customer_id,
                    "date_value": date_value,
                    "time_value": time_value,
                    "notes": notes_value,
                })

        if date_str and time_str:
            try:
                appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                if timezone.is_naive(appointment_datetime):
                    appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
                appointment.date = appointment_datetime
            except ValueError:
                messages.error(request, 'Invalid date or time format.')
                return render(request, "feature/appointment_form.html", {
                    "appointment": appointment,
                    "customers": customers,
                    "selected_customer_id": selected_customer_id,
                    "date_value": date_value,
                    "time_value": time_value,
                    "notes": notes_value,
                })

        appointment.notes = notes
        appointment.save()
        
        messages.success(request, 'Appointment updated successfully!')
        return redirect('feature:appointment_detail', appointment_id=appointment.id)
    
    return render(request, "feature/appointment_form.html", {
        "appointment": appointment,
        "customers": customers,
        "selected_customer_id": appointment.customer_id,
        "date_value": appointment.date.strftime('%Y-%m-%d') if appointment.date else '',
        "time_value": appointment.date.strftime('%H:%M') if appointment.date else '',
        "notes": appointment.notes,
    })


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


def notification_center(request):
    """Main notification page — visible to anonymous users with a signup prompt."""
    if request.user.is_authenticated:
        notifications = get_user_notifications(request.user, limit=50)
        unread_count = get_unread_count(request.user)
    else:
        notifications = []
        unread_count = 0

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'show_signup_prompt': not request.user.is_authenticated,
    }
    return render(request, "feature/notifications.html", context)


@login_required
def get_notifications_api(request):
    """AJAX endpoint to get notifications"""
    limit = request.GET.get('limit', 20)
    unread_only = request.GET.get('unread_only', False) == 'true'
    
    notifications = get_user_notifications(request.user, limit=int(limit), unread_only=unread_only)
    unread_count = get_unread_count(request.user)
    
    notifications_data = []
    for n in notifications:
        notifications_data.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'priority': n.priority,
            'time_ago': n.time_ago(),
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count,
        'total': notifications.count(),
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read"""
    mark_all_as_read(request.user)
    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return JsonResponse({'success': True})