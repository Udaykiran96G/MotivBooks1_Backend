from django.contrib import admin
from .models import (
    User, UserProgress, GoalDetails, ReadingAnalytics, UserProfile,
    ReadingPreference, Subscription, SavedQuote, DailyBoost,
    UserBadge, JournalEntry, Challenge, UserChallenge, Notification,
    Book, FeedPost, UserBook, Chapter, PasswordResetOTP,
    NotificationSetting, DeviceToken, LoginOTP, MindsetKB
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_staff')
    search_fields = ('email', 'name')

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'total_books_read')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_premium')
    list_filter = ('category', 'is_premium')
    search_fields = ('title', 'author')

@admin.register(MindsetKB)
class MindsetKBAdmin(admin.ModelAdmin):
    list_display = ('category', 'emotion', 'question', 'is_active')
    list_filter = ('category', 'emotion', 'is_active')
    search_fields = ('question', 'answer')

# Register remaining models with defaults
admin.site.register(GoalDetails)
admin.site.register(ReadingAnalytics)
admin.site.register(UserProfile)
admin.site.register(ReadingPreference)
admin.site.register(Subscription)
admin.site.register(SavedQuote)
admin.site.register(DailyBoost)
admin.site.register(UserBadge)
admin.site.register(JournalEntry)
admin.site.register(Challenge)
admin.site.register(UserChallenge)
admin.site.register(Notification)
admin.site.register(FeedPost)
admin.site.register(UserBook)
admin.site.register(Chapter)
admin.site.register(PasswordResetOTP)
admin.site.register(NotificationSetting)
admin.site.register(DeviceToken)
admin.site.register(LoginOTP)
