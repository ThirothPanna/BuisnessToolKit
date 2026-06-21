from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Appointment, Invoice, Customer, Notification
from .notification_utils import create_notification

@receiver(post_save, sender=Appointment)
def appointment_notification(sender, instance, created, **kwargs):
    # Only proceed if the appointment has a user
    if not instance.user:
        return
        
    if created:
        # New appointment created
        create_notification(
            user=instance.user,
            notification_type='appointment',
            title='New Appointment Created',
            message=f"You scheduled an appointment with {instance.customer.name} on {instance.date.strftime('%B %d, %Y')} at {instance.date.strftime('%I:%M %p')}",
            obj=instance,
            priority='medium'
        )
        print(f"[OK] Notification created for new appointment: {instance.customer.name}")  # Debug
    else:
        # Appointment updated
        create_notification(
            user=instance.user,
            notification_type='appointment',
            title='Appointment Updated',
            message=f"Your appointment with {instance.customer.name} has been updated to {instance.date.strftime('%B %d, %Y')} at {instance.date.strftime('%I:%M %p')}",
            obj=instance,
            priority='low'
        )
        print(f"[OK] Notification created for updated appointment: {instance.customer.name}")  # Debug

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
    print(f"[OK] Notification created for cancelled appointment: {instance.customer.name}")  # Debug

@receiver(post_save, sender=Invoice)
def invoice_notification(sender, instance, created, **kwargs):
    # Only proceed if the invoice has a user
    if not instance.user:
        return
        
    if created:
        # New invoice created
        create_notification(
            user=instance.user,
            notification_type='invoice',
            title='New Invoice Created',
            message=f"Invoice #{instance.id} for {instance.customer.name} - Amount: ${instance.amount}",
            obj=instance,
            priority='medium'
        )
        print(f"[OK] Notification created for new invoice: #{instance.id}")  # Debug
    elif instance.status == 'paid':
        # Invoice marked as paid
        create_notification(
            user=instance.user,
            notification_type='invoice',
            title='Invoice Paid',
            message=f"Invoice #{instance.id} for {instance.customer.name} has been paid",
            obj=instance,
            priority='high'
        )
        print(f"[OK] Notification created for paid invoice: #{instance.id}")  # Debug
