from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import NotificationSetting, FeedPost
from .utils import send_push_notification
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_notification_settings(sender, instance, created, **kwargs):
    """
    Automatically create default NotificationSetting for every new user.
    """
    if created:
        NotificationSetting.objects.get_or_create(user=instance)
        logger.info(f"Notification settings initialized for user {instance.email}")

@receiver(post_save, sender=FeedPost)
def notify_new_feed_post(sender, instance, created, **kwargs):
    """
    Example trigger: Notify all users about a new feed post.
    In a real app, you might only notify followers or specific segments.
    """
    if created:
        logger.info(f"New FeedPost created: {instance.content[:30]}... Triggering notifications.")
        
        # For demonstration purposes, we'll try to notify the post author
        # (Assuming the post has an 'author' or user field, but looking at FeedPost model might be better)
        # Based on previous research, FeedPost has no direct user field in my previous search?
        # Let me check current users to send a test notification.
        
        title = "New Inspiration Shared!"
        message = f"Check out the latest post: {instance.content[:50]}"
        
        # Test notification for all users who have push_notifications enabled
        # This is for demo/example use
        target_users = User.objects.all()
        for user in target_users:
            # send_push_notification handles preference check internally
            send_push_notification(user, title, message, notification_type='general')
