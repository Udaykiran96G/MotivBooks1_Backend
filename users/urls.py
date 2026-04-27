from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from .views import (
    RegisterView, CustomTokenObtainPairView, AdminLoginView, AdminRegisterView,
    UserProgressView, GoalDetailsView, 
    ReadingAnalyticsView, SavedQuotesView, DashboardView, 
    DailyBoostView, UserBadgesView, JournalEntryView, HomeFeedView,
    UserProfileView, ReadingPreferenceView, SubscriptionView, 
    GrowthStatsView, ProfileDetailView,
    ChallengeListView, ChallengeUpdateView, NotificationListView,
    LibraryView, AICoachInsightView, AICoachChatView, AICoachStrategyView,
    AISummaryView, UpdateReadingProgressView,
    CompletedBooksView, BookDetailView,
    ChapterListView, TrackBookOpenView, MoodGraphView,
    ForgotPasswordView, VerifyOTPView, ResetPasswordView, ChangePasswordView,
    DeleteAccountView, SavedQuoteDetailView,
    NotificationSettingView, DeviceTokenView, TranslateView,
    SendLoginOTPView, LoginWithOTPView,
    AdminBookListCreateView, AdminBookDeleteView, AdminChapterListCreateView
)


# CustomTokenObtainPairSerializer and CustomTokenObtainPairView moved to views.py


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('login/send-otp/', SendLoginOTPView.as_view(), name='send_login_otp'),
    path('login/verify-otp/', LoginWithOTPView.as_view(), name='login_with_otp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('progress/', UserProgressView.as_view(), name='progress'),
    path('progress/goal-details/', GoalDetailsView.as_view(), name='goal_details'),
    path('progress/reading-analytics/', ReadingAnalyticsView.as_view(), name='reading_analytics'),
    path('progress/saved-quotes/', SavedQuotesView.as_view(), name='saved_quotes'),
    path('progress/saved-quotes/<int:quote_id>/', SavedQuoteDetailView.as_view(), name='saved_quote_detail'),
    path('progress/mood-graph/', MoodGraphView.as_view(), name='mood_graph'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/daily-boost/', DailyBoostView.as_view(), name='daily_boost'),
    path('dashboard/badges/', UserBadgesView.as_view(), name='user_badges'),
    path('dashboard/journal/', JournalEntryView.as_view(), name='journal_entries'),
    path('feed/', HomeFeedView.as_view(), name='home_feed'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/detail/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/delete/', DeleteAccountView.as_view(), name='profile_delete'),
    path('profile/preferences/', ReadingPreferenceView.as_view(), name='preferences'),
    path('profile/subscription/', SubscriptionView.as_view(), name='subscription'),
    path('profile/growth-stats/', GrowthStatsView.as_view(), name='growth_stats'),
    path('challenges/', ChallengeListView.as_view(), name='challenges'),
    path('challenges/<int:challenge_id>/update/', ChallengeUpdateView.as_view(), name='challenge_update'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('library/', LibraryView.as_view(), name='library'),
    path('library/completed/', CompletedBooksView.as_view(), name='completed_books'),
    path('books/<int:book_id>/', BookDetailView.as_view(), name='book_detail'),
    path('books/<int:book_id>/chapters/', ChapterListView.as_view(), name='book_chapters'),
    path('books/track-open/', TrackBookOpenView.as_view(), name='track_book_open'),
    path('ai-coach/insight/', AICoachInsightView.as_view(), name='ai_coach_insight'),
    path('ai-coach/chat/', AICoachChatView.as_view(), name='ai_coach_chat'),
    path('ai-coach/strategy/', AICoachStrategyView.as_view(), name='ai_coach_strategy'),
    path('ai-coach/summary/', AISummaryView.as_view(), name='ai_coach_summary'),
    path('translate/', TranslateView.as_view(), name='translate'),
    path('profile/notifications/', NotificationSettingView.as_view(), name='notification_settings'),
    path('notifications/device-token/', DeviceTokenView.as_view(), name='device_token'),
    path('books/track-progress/', UpdateReadingProgressView.as_view(), name='track_progress'),

    # Admin endpoints
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin/register/', AdminRegisterView.as_view(), name='admin_register'),
    path('admin/books/', AdminBookListCreateView.as_view(), name='admin_books'),
    path('admin/books/<int:book_id>/', AdminBookDeleteView.as_view(), name='admin_book_delete'),
    path('admin/books/<int:book_id>/chapters/', AdminChapterListCreateView.as_view(), name='admin_chapters'),
]

