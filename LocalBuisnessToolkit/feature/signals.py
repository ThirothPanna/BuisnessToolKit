from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Appointment, Invoice, Customer, Notification
from .notification_utils import create_notification

# ========== APPOINTMENT SIGNALS ==========

@receiver(post_save, sender=Appointment)
def appointment_notification(sender, instance, created, **kwargs):
    if not instance.user:
        return
        
    if created:
        create_notification(
            user=instance.user,
            notification_type='appointment',
            title='New Appointment Created',
            message=f"You scheduled an appointment with {instance.customer.name} on {instance.date.strftime('%B %d, %Y')} at {instance.date.strftime('%I:%M %p')}",
            obj=instance,
            priority='medium'
        )
        print(f"[OK] Notification created for new appointment: {instance.customer.name}")
    else:
        create_notification(
            user=instance.user,
            notification_type='appointment',
            title='Appointment Updated',
            message=f"Your appointment with {instance.customer.name} has been updated to {instance.date.strftime('%B %d, %Y')} at {instance.date.strftime('%I:%M %p')}",
            obj=instance,
            priority='low'
        )
        print(f"[OK] Notification created for updated appointment: {instance.customer.name}")

@receiver(post_delete, sender=Appointment)
def appointment_deleted_notification(sender, instance, **kwargs):
    if not instance.user:
        return
        
    create_notification(
        user=instance.user,
        notification_type='appointment',
        title='Appointment Cancelled',
        message=f"Your appointment with {instance.customer.name} on {instance.date.strftime('%B %d, %Y')} was cancelled",
        obj=None,
        priority='high'
    )
    print(f"[OK] Notification created for cancelled appointment: {instance.customer.name}")

# ========== CUSTOMER SIGNALS ==========

@receiver(post_save, sender=Customer)
def customer_notification(sender, instance, created, **kwargs):
    if not instance.owner:
        return
        
    if created:
        create_notification(
            user=instance.owner,
            notification_type='customer',
            title='New Customer Added',
            message=f"You added a new customer: {instance.name} ({instance.email})",
            obj=instance,
            priority='medium'
        )
        print(f"[OK] Notification created for new customer: {instance.name}")
    else:
        create_notification(
            user=instance.owner,
            notification_type='customer',
            title='Customer Updated',
            message=f"Customer {instance.name}'s information has been updated",
            obj=instance,
            priority='low'
        )
        print(f"[OK] Notification created for updated customer: {instance.name}")

@receiver(post_delete, sender=Customer)
def customer_deleted_notification(sender, instance, **kwargs):
    if not instance.owner:
        return
        
    create_notification(
        user=instance.owner,
        notification_type='customer',
        title='Customer Deleted',
        message=f"You deleted customer: {instance.name} ({instance.email})",
        obj=None,
        priority='high'
    )
    print(f"[OK] Notification created for deleted customer: {instance.name}")

# ========== INVOICE SIGNALS - ALWAYS SHOWS STATUS ==========

@receiver(post_save, sender=Invoice)
def invoice_notification(sender, instance, created, **kwargs):
    if not instance.user:
        print(f"❌ Invoice #{instance.id} has NO user - skipping")
        return
    
    print(f"🔔 INVOICE SIGNAL - ID: {instance.id}, Created: {created}, Status: '{instance.status}'")
    
    # Status emoji map
    status_emoji = {
        'paid': '✅',
        'unpaid': '❌',
        'pending': '⏳',
        'overdue': '⚠️'
    }
    status_text = {
        'paid': 'Paid',
        'unpaid': 'Unpaid',
        'pending': 'Pending',
        'overdue': 'Overdue'
    }
    
    # --- CASE 1: NEW INVOICE CREATED ---
    if created:
        # Send "New Invoice Created"
        create_notification(
            user=instance.user,
            notification_type='invoice',
            title='New Invoice Created',
            message=f"Invoice #{instance.id} for {instance.customer.name} - Amount: ${instance.amount} ({status_text.get(instance.status, instance.status)})",
            obj=instance,
            priority='medium'
        )
        print(f"[OK] Notification created for NEW invoice: #{instance.id}")
        return
    
    # --- CASE 2: EXISTING INVOICE UPDATED ---
    try:
        old_instance = Invoice.objects.get(pk=instance.pk)
        
        # Build the message
        message_parts = []
        changes = []
        
        # Check status change
        if old_instance.status != instance.status:
            old_status = status_text.get(old_instance.status, old_instance.status)
            new_status = status_text.get(instance.status, instance.status)
            old_emoji = status_emoji.get(old_instance.status, '')
            new_emoji = status_emoji.get(instance.status, '')
            changes.append(f"status changed from {old_status} {old_emoji} to {new_status} {new_emoji}")
        
        # Check amount change
        if old_instance.amount != instance.amount:
            changes.append(f"amount changed from ${old_instance.amount} to ${instance.amount}")
        
        # Check customer change
        if old_instance.customer_id != instance.customer_id:
            changes.append(f"customer changed to {instance.customer.name}")
        
        # Check due date change
        if old_instance.due_date != instance.due_date:
            old_date = old_instance.due_date.strftime('%b %d, %Y') if old_instance.due_date else 'Not set'
            new_date = instance.due_date.strftime('%b %d, %Y') if instance.due_date else 'Not set'
            changes.append(f"due date changed from {old_date} to {new_date}")
        
        # Build notification
        if changes:
            # Status change - use specific title
            if old_instance.status != instance.status:
                new_status = status_text.get(instance.status, instance.status)
                new_emoji = status_emoji.get(instance.status, '')
                
                if instance.status == 'paid':
                    title = 'Invoice Paid'
                    message = f"Invoice #{instance.id} for {instance.customer.name} has been paid! 🎉"
                elif instance.status == 'overdue':
                    title = 'Invoice Overdue'
                    message = f"Invoice #{instance.id} for {instance.customer.name} is now Overdue! ⚠️"
                elif instance.status == 'unpaid':
                    title = 'Invoice Status: Unpaid'
                    message = f"Invoice #{instance.id} for {instance.customer.name} is now Unpaid ❌"
                elif instance.status == 'pending':
                    title = 'Invoice Status: Pending'
                    message = f"Invoice #{instance.id} for {instance.customer.name} is now Pending ⏳"
                else:
                    title = 'Invoice Updated'
                    message = f"Invoice #{instance.id} updated: {', '.join(changes)}"
            else:
                # Non-status change
                title = 'Invoice Updated'
                message = f"Invoice #{instance.id} updated: {', '.join(changes)}"
            
            create_notification(
                user=instance.user,
                notification_type='invoice',
                title=title,
                message=message,
                obj=instance,
                priority='low' if 'amount' in str(changes) and 'status' not in str(changes) else 'high' if instance.status in ['paid', 'overdue'] else 'medium'
            )
            print(f"[OK] Notification created: {title}")
        else:
            # No changes detected - still send notification with current status
            current_status = status_text.get(instance.status, instance.status)
            current_emoji = status_emoji.get(instance.status, '')
            create_notification(
                user=instance.user,
                notification_type='invoice',
                title='Invoice Updated',
                message=f"Invoice #{instance.id} for {instance.customer.name} - Current Status: {current_status} {current_emoji}",
                obj=instance,
                priority='low'
            )
            print(f"[OK] Notification created for updated invoice (no changes): {instance.id}")
                
    except Invoice.DoesNotExist:
        print(f"❌ Could not find old invoice state for #{instance.id}")
    except Exception as e:
        print(f"❌ Error in invoice_notification: {e}")
        # Fallback
        current_status = status_text.get(instance.status, instance.status)
        create_notification(
            user=instance.user,
            notification_type='invoice',
            title='Invoice Updated',
            message=f"Invoice #{instance.id} for {instance.customer.name} - Status: {current_status}",
            obj=instance,
            priority='low'
        )
        print(f"[OK] Notification created for updated invoice (fallback): #{instance.id}")

@receiver(post_delete, sender=Invoice)
def invoice_deleted_notification(sender, instance, **kwargs):
    if not instance.user:
        return
        
    create_notification(
        user=instance.user,
        notification_type='invoice',
        title='Invoice Deleted',
        message=f"Invoice #{instance.id} for {instance.customer.name} (${instance.amount}) was deleted",
        obj=None,
        priority='high'
    )
    print(f"[OK] Notification created for deleted invoice: #{instance.id}")
    
    if instance.customer and instance.customer.owner and instance.customer.owner != instance.user:
        create_notification(
            user=instance.customer.owner,
            notification_type='invoice',
            title='Invoice Deleted',
            message=f"Invoice #{instance.id} for {instance.customer.name} was deleted",
            obj=None,
            priority='high'
        )
        print(f"[OK] Notification created for customer owner: #{instance.id}")