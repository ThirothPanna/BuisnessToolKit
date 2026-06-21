from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from datetime import datetime
from .models import Appointment, Customer, Invoice, Notification
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .notification_utils import get_user_notifications, mark_all_as_read, get_unread_count


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
        try:
            # Get data safely
            customers = Customer.objects.filter(owner=request.user)
            appointments = Appointment.objects.filter(customer__owner=request.user)
            notifications = Notification.objects.filter(user=request.user)
            
            # Handle invoices with error protection
            try:
                invoices = Invoice.objects.filter(customer__owner=request.user)
                
                # Filter valid invoices only
                valid_invoices = []
                for inv in invoices:
                    try:
                        # Test if amount is valid
                        float(inv.amount)
                        valid_invoices.append(inv)
                    except (ValueError, TypeError, InvalidOperation):
                        # Skip invalid invoices
                        continue
                
                # Count unpaid invoices
                invoices_unpaid_count = sum(1 for inv in valid_invoices if inv.status == "unpaid")
                
                # Get recent invoices (sorted by created_at)
                recent_invoices = sorted(valid_invoices, key=lambda x: x.created_at, reverse=True)[:5]
                
            except Exception as e:
                print(f"Invoice error: {e}")
                invoices_unpaid_count = 0
                recent_invoices = []
            
            context = {
                "message": f"Welcome {request.user.username}",
                "appointments_count": appointments.count(),
                "customers_count": customers.count(),
                "invoices_unpaid": invoices_unpaid_count,
                "notifications_count": notifications.count(),
                "recent_appointments": appointments.order_by("-date")[:5],
                "recent_invoices": recent_invoices,
                "user_logged_in": True,
            }
        except Exception as e:
            print(f"Dashboard error: {e}")
            context = {
                "message": f"Welcome {request.user.username}",
                "appointments_count": 0,
                "customers_count": 0,
                "invoices_unpaid": 0,
                "notifications_count": 0,
                "recent_appointments": [],
                "recent_invoices": [],
                "user_logged_in": True,
            }
    else:
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
def customer_detail(request, customer_id):
    """View a single customer (detail page with actions)."""
    if not request.user.is_authenticated:
        return redirect('account_login')

    customer = get_object_or_404(Customer, id=customer_id, owner=request.user)
    return render(request, "feature/customer_detail.html", {"customer": customer})


@login_required
def customer_edit(request, customer_id):
    """Edit a customer."""
    customer = get_object_or_404(Customer, id=customer_id, owner=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        if not name or not email:
            messages.error(request, 'Name and Email are required fields.')
            return render(request, "feature/customer_form.html", {"customer": customer})

        # unique per owner/email
        if Customer.objects.filter(owner=request.user, email=email).exclude(id=customer.id).exists():
            messages.warning(request, f'A customer with email "{email}" already exists.')
            return render(request, "feature/customer_form.html", {"customer": customer})

        customer.name = name
        customer.email = email
        customer.phone = phone or ''
        customer.save()

        messages.success(request, 'Customer updated successfully!')
        return redirect('feature:customer_detail', customer_id=customer.id)

    return render(request, "feature/customer_form.html", {"customer": customer})


@login_required
def customer_delete(request, customer_id):
    """Delete a customer (confirmation page + POST deletion)."""
    customer = get_object_or_404(Customer, id=customer_id, owner=request.user)

    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully!')
        return redirect('feature:customers')

    return render(request, "feature/customer_confirm_delete.html", {"customer": customer})


@login_required
def customer_create(request):
    """Create a new customer (appointment-like feature parity)."""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        if not name or not email:
            messages.error(request, 'Name and Email are required fields.')
            return redirect('feature:customer_create')

        if Customer.objects.filter(owner=request.user, email=email).exists():
            messages.warning(request, f'A customer with email "{email}" already exists.')
            return redirect('feature:customer_create')

        customer = Customer.objects.create(
            name=name,
            email=email,
            phone=phone or '',
            owner=request.user,
        )

        messages.success(request, f'Customer "{customer.name}" added successfully!')
        return redirect('feature:customer_detail', customer_id=customer.id)

    # GET: show empty create form
    return render(request, "feature/customer_form.html", {"customer": None})


@login_required
def add_customer(request):
    """Backward-compatible alias for the modal/form action."""
    return customer_create(request)



def invoices(request):
    """Anyone can VIEW invoices list, but to manage need login"""
    if request.user.is_authenticated:
        try:
            invoices = Invoice.objects.filter(
                Q(customer__owner=request.user) | Q(user=request.user)
            ).distinct()

            # Check for and remove problematic invoices
            for invoice in list(invoices):
                try:
                    float(invoice.amount)
                except (ValueError, TypeError, InvalidOperation):
                    invoice.delete()
                    messages.warning(request, f'Removed invalid invoice #{invoice.id}')

            # Refresh queryset after cleanup
            invoices = Invoice.objects.filter(
                Q(customer__owner=request.user) | Q(user=request.user)
            ).distinct()

            customers = Customer.objects.filter(owner=request.user)
            context = {
                "invoices": invoices,
                "invoices_count": invoices.count(),
                "invoices_unpaid": invoices.filter(status="unpaid").count(),
                "invoices_paid": invoices.filter(status="paid").count(),
                "customers": customers,
                "user_logged_in": True,
            }
        except Exception:
            messages.error(request, 'Error loading invoices. Please try again.')
            context = {
                "invoices": [],
                "invoices_count": 0,
                "invoices_unpaid": 0,
                "invoices_paid": 0,
                "customers": [],
                "user_logged_in": True,
            }
    else:
        context = {
            "invoices": [],
            "invoices_count": 0,
            "invoices_unpaid": 0,
            "invoices_paid": 0,
            "customers": [],
            "user_logged_in": False,
            "login_required": True,
        }

    return render(request, "feature/invoices.html", context)


@login_required
def invoice_detail(request, invoice_id):
    """View invoice details"""
    invoice = get_object_or_404(
        Invoice,
        Q(customer__owner=request.user) | Q(user=request.user),
        id=invoice_id,
    )
    return render(request, "feature/invoice_detail.html", {"invoice": invoice})


@login_required
def invoice_delete(request, invoice_id):
    """Delete an invoice (POST only) and notify both staff + customer owner."""
    invoice = get_object_or_404(
        Invoice,
        Q(customer__owner=request.user) | Q(user=request.user),
        id=invoice_id,
    )

    if request.method == 'POST':
        customer_owner = getattr(invoice.customer, 'owner', None)

        # delete notification: notify staff user (invoice.user if present, else request.user) and customer owner
        notify_users = set()
        if invoice.user_id:
            notify_users.add(invoice.user_id)
        notify_users.add(request.user.id)
        if customer_owner and customer_owner.id:
            notify_users.add(customer_owner.id)

        from django.contrib.auth import get_user_model
        from .notification_utils import create_notification

        UserModel = get_user_model()
        for uid in notify_users:
            u = UserModel.objects.get(id=uid)
            create_notification(
                user=u,
                notification_type='invoice',
                title='Invoice Deleted',
                message=f"Invoice #{invoice.id} for {invoice.customer.name} was deleted.",
                obj=None,
                priority='high',
            )


        invoice.delete()
        messages.success(request, f'Invoice #{invoice_id} deleted successfully!')
        return redirect('feature:invoices')

    return render(request, "feature/invoice_confirm_delete.html", {"invoice": invoice})


@login_required
def invoice_edit(request, invoice_id):
    """Edit an invoice"""
    invoice = get_object_or_404(
        Invoice,
        Q(customer__owner=request.user) | Q(user=request.user),
        id=invoice_id,
    )
    customers = Customer.objects.filter(owner=request.user)


    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        amount = request.POST.get('amount')
        status = request.POST.get('status')
        description = request.POST.get('description', '')
        due_date = request.POST.get('due_date')

        if not customer_id:
            messages.error(request, 'Please select a customer.')
            return render(request, "feature/invoice_form.html", {
                "invoice": invoice,
                "customers": customers,
                "status_choices": Invoice.STATUS_CHOICES,
            })

        try:
            customer = Customer.objects.get(id=customer_id, owner=request.user)
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid customer selected.')
            return render(request, "feature/invoice_form.html", {
                "invoice": invoice,
                "customers": customers,
                "status_choices": Invoice.STATUS_CHOICES,
            })

        try:
            amount_value = Decimal(amount)
        except (InvalidOperation, TypeError):
            messages.error(request, 'Please enter a valid amount greater than 0.')
            return render(request, "feature/invoice_form.html", {
                "invoice": invoice,
                "customers": customers,
                "status_choices": Invoice.STATUS_CHOICES,
            })

        if amount_value <= 0:
            messages.error(request, 'Please enter a valid amount greater than 0.')
            return render(request, "feature/invoice_form.html", {
                "invoice": invoice,
                "customers": customers,
                "status_choices": Invoice.STATUS_CHOICES,
            })

        due_date_value = None
        if due_date:
            try:
                due_date_value = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Please enter a valid due date.')
                return render(request, "feature/invoice_form.html", {
                    "invoice": invoice,
                    "customers": customers,
                    "status_choices": Invoice.STATUS_CHOICES,
                })

        invoice.customer = customer
        invoice.amount = amount_value
        invoice.status = status
        invoice.description = description
        invoice.due_date = due_date_value
        invoice.user = request.user
        invoice.save()

        messages.success(request, f'Invoice #{invoice.id} updated successfully!')
        return redirect('feature:invoice_detail', invoice_id=invoice.id)

    return render(request, "feature/invoice_form.html", {
        "invoice": invoice,
        "customers": customers,
        "status_choices": Invoice.STATUS_CHOICES,
    })


@login_required
def add_invoice(request):
    """Add a new invoice"""
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        amount = request.POST.get('amount')
        status = request.POST.get('status')
        description = request.POST.get('description', '')
        due_date = request.POST.get('due_date')
        
        # Validation
        if not customer_id:
            messages.error(request, 'Please select a customer.')
            return redirect('feature:invoices')
        
        try:
            amount_value = Decimal(amount)
        except (InvalidOperation, TypeError):
            messages.error(request, 'Please enter a valid amount greater than 0.')
            return redirect('feature:invoices')

        if amount_value <= 0:
            messages.error(request, 'Please enter a valid amount greater than 0.')
            return redirect('feature:invoices')
        
        if not status:
            messages.error(request, 'Please select a status.')
            return redirect('feature:invoices')
        
        # Check if customer exists and belongs to this user
        try:
            customer = Customer.objects.get(id=customer_id, owner=request.user)
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid customer selected.')
            return redirect('feature:invoices')
        
        due_date_value = None
        if due_date:
            try:
                due_date_value = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Please enter a valid due date.')
                return redirect('feature:invoices')

        # Create the invoice
        invoice = Invoice.objects.create(
            customer=customer,
            amount=amount_value,
            status=status,
            description=description,
            user=request.user,
            due_date=due_date_value,
        )

        messages.success(request, f'Invoice #{invoice.id} created successfully for {customer.name}!')
        return redirect('feature:invoices')
    
    # If not POST, redirect back to invoices page
    return redirect('feature:invoices')


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
        
        appointment_notifications = request.POST.get('appointment_notifications') == 'on'
        invoice_notifications = request.POST.get('invoice_notifications') == 'on'
        customer_notifications = request.POST.get('customer_notifications') == 'on'
        reminder_notifications = request.POST.get('reminder_notifications') == 'on'
        system_notifications = request.POST.get('system_notifications') == 'on'
        
        request.session['notification_preferences'] = {
            'appointment_notifications': appointment_notifications,
            'invoice_notifications': invoice_notifications,
            'customer_notifications': customer_notifications,
            'reminder_notifications': reminder_notifications,
            'system_notifications': system_notifications,
        }
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.save()
        
        messages.success(request, 'Settings updated successfully!')
        return redirect('feature:settings')
    
    # Get preferences from session
    user_preferences = request.session.get('notification_preferences', {
        'appointment_notifications': True,
        'invoice_notifications': True,
        'customer_notifications': True,
        'reminder_notifications': True,
        'system_notifications': True,
    })
    
    context = {
        "user": user,
        "user_preferences": user_preferences,
        "customers_count": Customer.objects.filter(owner=user).count(),
        "appointments_count": Appointment.objects.filter(user=user).count(),
        "invoices_count": Invoice.objects.filter(user=user).count(),
        "unread_notifications": Notification.objects.filter(user=user, is_read=False).count(),
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
