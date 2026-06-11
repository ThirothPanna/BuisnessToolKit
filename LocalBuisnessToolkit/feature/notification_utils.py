from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

def create_notification(user, notification_type, title, message, obj=None, priority='medium'):
    """Helper function to create notifications"""
    from .models import Notification
    
    notification = Notification(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority
    )
    
    if obj:
        content_type = ContentType.objects.get_for_model(obj)
        notification.content_type = content_type
        notification.object_id = obj.id
        notification.content_object = obj
    
    notification.save()
    return notification

def get_user_notifications(user, limit=20, unread_only=False):
    """Get notifications for a user"""
    from .models import Notification
    
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    if unread_only:
        notifications = notifications.filter(is_read=False)
    return notifications[:limit]

def mark_all_as_read(user):
    """Mark all notifications as read for a user"""
    from .models import Notification
    
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)

def get_unread_count(user):
    """Get count of unread notifications"""
    from .models import Notification
    
    return Notification.objects.filter(user=user, is_read=False).count()