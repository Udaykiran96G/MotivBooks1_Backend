import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
firebase_creds_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')

if os.path.exists(firebase_creds_path):
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_creds_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {e}")
else:
    logger.warning(f"Firebase credentials not found at {firebase_creds_path}. FCM functionality will be limited.")

def send_push_notification(user, title, message, notification_type='general'):
    """
    Sends a push notification to all devices belonging to a user,
    respecting their notification preferences.
    """
    from .models import DeviceToken, NotificationSetting
    
    try:
        # 1. Check user notification preferences
        settings_obj, _ = NotificationSetting.objects.get_or_create(user=user)
        
        if not settings_obj.push_notifications:
            logger.info(f"User {user.email} has disabled all push notifications.")
            return False
            
        # Check specific notification type preferences
        is_type_enabled = True
        if notification_type == 'daily_reading_reminder':
            is_type_enabled = settings_obj.daily_reading_reminder
        elif notification_type == 'streak_protection_alert':
            is_type_enabled = settings_obj.streak_protection_alert
        elif notification_type == 'goal_based_reminder':
            is_type_enabled = settings_obj.goal_based_reminder
        elif notification_type == 'weekly_growth_report':
            is_type_enabled = settings_obj.weekly_growth_report
            
        if not is_type_enabled:
            logger.info(f"Notification type '{notification_type}' is disabled for user {user.email}.")
            return False

        # 2. Retrieve device tokens for the user
        device_tokens = DeviceToken.objects.filter(user=user).values_list('device_token', flat=True)
        
        if not device_tokens:
            logger.info(f"No device tokens registered for user {user.email}.")
            return False

        # 3. Send notification to each registered device
        success_count = 0
        for token in device_tokens:
            try:
                fcm_message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=message,
                    ),
                    token=token,
                    data={
                        'notification_type': notification_type,
                        'click_action': 'FLUTTER_NOTIFICATION_CLICK', # Adjust based on frontend needs
                    }
                )
                response = messaging.send(fcm_message)
                logger.info(f"Successfully sent FCM to {user.email} (token: {token[:10]}...): {response}")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send FCM to token {token[:10]}...: {e}")
                # Optional: Remove invalid tokens if FCM returns specific error
                # if "registration-token-not-registered" in str(e):
                #     DeviceToken.objects.filter(device_token=token).delete()

        return success_count > 0

    except Exception as e:
        logger.error(f"Unexpected error in send_push_notification: {e}")
        return False

def validate_password_strength(password):
    """
    Validates that a password meets the strength requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    import re
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, ""
