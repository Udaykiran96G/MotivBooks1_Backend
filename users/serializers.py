from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserProgress, GoalDetails, ReadingAnalytics, SavedQuote, 
    UserBadge, JournalEntry, Book, FeedPost, UserBook, DailyBoost,
    UserProfile, ReadingPreference, Subscription,
    Challenge, UserChallenge, Notification, Chapter,
    NotificationSetting, DeviceToken
)

User = get_user_model()

class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = (
            'push_notifications', 'email_notifications', 
            'daily_reading_reminder', 'streak_protection_alert', 
            'goal_based_reminder', 'weekly_growth_report'
        )

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ('device_token',)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'is_staff')

class UserProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('name', 'email', 'phone', 'dob', 'location', 'avatar_url', 'member_since')
        read_only_fields = ('member_since',)

class ReadingPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingPreference
        fields = ('font_size', 'theme', 'language', 'auto_save_highlights', 'interests', 'improvement_goals', 'reading_style')

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('plan_type', 'status', 'expiry_date')
        read_only_fields = ('expiry_date',)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirmPassword = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('name', 'email', 'password', 'confirmPassword', 'phone')

    def validate_phone(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Mobile number must be exactly 10 digits.")
        return value

    def validate_password(self, value):
        from .utils import validate_password_strength
        is_strong, message = validate_password_strength(value)
        if not is_strong:
            raise serializers.ValidationError(message)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirmPassword']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        # Create profile with phone
        from .models import UserProfile
        UserProfile.objects.create(user=user, phone=validated_data['phone'])
        return user

class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = '__all__'
        read_only_fields = ('user',)

class GoalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalDetails
        fields = '__all__'
        read_only_fields = ('user',)

class ReadingAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingAnalytics
        fields = '__all__'
        read_only_fields = ('user',)

class SavedQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedQuote
        fields = '__all__'
        read_only_fields = ('user',)

class DailyBoostSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyBoost
        fields = '__all__'

class UserBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBadge
        fields = '__all__'
        read_only_fields = ('user',)

class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = '__all__'
        read_only_fields = ('user',)

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class UserBookSerializer(serializers.ModelSerializer):
    book_details = BookSerializer(source='book', read_only=True)
    
    class Meta:
        model = UserBook
        fields = '__all__'
        read_only_fields = ('user',)


class FeedPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedPost
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('user',)

class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = '__all__'

class UserChallengeSerializer(serializers.ModelSerializer):
    challenge_details = ChallengeSerializer(source='challenge', read_only=True)
    
    class Meta:
        model = UserChallenge
        fields = '__all__'
        read_only_fields = ('user',)

class ProfileDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    preferences = ReadingPreferenceSerializer(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)
    progress = UserProgressSerializer(read_only=True)
    analytics = ReadingAnalyticsSerializer(source='reading_analytics', read_only=True)
    notification_settings = NotificationSettingSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'profile', 'preferences', 'subscription', 'progress', 'analytics', 'notification_settings')

class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = '__all__'


class AdminBookUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'description', 'category', 'cover_url', 'is_premium', 'genre', 'pdf_file')
        read_only_fields = ('id',)


class AdminChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ('id', 'title', 'content', 'order')
        read_only_fields = ('id',)
