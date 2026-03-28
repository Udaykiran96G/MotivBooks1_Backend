from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.mail import send_mail
import random
import logging
import json
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)
from .quotes import QUOTES_DATA, INTEREST_MAP, GOAL_MAP
from .models import (
    UserProgress, GoalDetails, ReadingAnalytics, SavedQuote, 
    Book, FeedPost, UserBadge, JournalEntry, DailyBoost,
    UserProfile, ReadingPreference, Subscription,
    Challenge, UserChallenge, Notification, Chapter, UserBook,
    NotificationSetting, DeviceToken
)
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserProgressSerializer, 
    GoalDetailsSerializer, ReadingAnalyticsSerializer, SavedQuoteSerializer,
    BookSerializer, FeedPostSerializer, UserBadgeSerializer, DailyBoostSerializer,
    JournalEntrySerializer, UserProfileSerializer, ReadingPreferenceSerializer,
    SubscriptionSerializer, ProfileDetailSerializer, UserBookSerializer,
    ChallengeSerializer, UserChallengeSerializer, NotificationSerializer,
    ChapterSerializer,
    NotificationSettingSerializer, DeviceTokenSerializer
)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Also update User model name if provided
            name = request.data.get('name')
            if name:
                request.user.name = name
                request.user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReadingPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs, _ = ReadingPreference.objects.get_or_create(user=request.user)
        serializer = ReadingPreferenceSerializer(prefs)
        return Response(serializer.data)

    def patch(self, request):
        prefs, _ = ReadingPreference.objects.get_or_create(user=request.user)
        serializer = ReadingPreferenceSerializer(prefs, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub, _ = Subscription.objects.get_or_create(user=request.user)
        serializer = SubscriptionSerializer(sub)
        return Response(serializer.data)

    def post(self, request):
        sub, _ = Subscription.objects.get_or_create(user=request.user)
        serializer = SubscriptionSerializer(sub, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GrowthStatsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        progress, _ = UserProgress.objects.get_or_create(user=user)
        analytics, _ = ReadingAnalytics.objects.get_or_create(user=user)
        
        # Calculate reading time string
        hours = progress.total_hours_read or 0
        minutes = analytics.daily_average_minutes or 0
        
        data = {
            "streakDays": progress.current_streak,
            "booksRead": progress.total_books_read,
            "quotesSaved": progress.total_quotes_saved,
            "goalProgress": 65 if progress.active_goal_total_books == 0 else int((progress.active_goal_books_completed / progress.active_goal_total_books) * 100),
            "weeklyImprovement": analytics.weekly_improvement_percentage,
            "totalReadingTime": f"{hours}h {minutes % 60}m",
            "pagesRead": analytics.pages_read,
            "notesTaken": progress.total_notes_taken,
            "dailyProgress": [
                analytics.mon_progress, analytics.tue_progress, analytics.wed_progress,
                analytics.thu_progress, analytics.fri_progress, analytics.sat_progress,
                analytics.sun_progress
            ]
        }
        return Response(data)

class ProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info(f"Fetching profile detail for user: {request.user.email}")
        try:
            # Ensure all components exist
            UserProfile.objects.get_or_create(user=request.user)
            ReadingPreference.objects.get_or_create(user=request.user)
            Subscription.objects.get_or_create(user=request.user)
            UserProgress.objects.get_or_create(user=request.user)
            ReadingAnalytics.objects.get_or_create(user=request.user)
            
            serializer = ProfileDetailSerializer(request.user)
            data = serializer.data
            logger.info(f"Successfully serialized profile detail for user: {request.user.email}")
            return Response(data)
        except Exception as e:
            logger.error(f"Error fetching profile detail for {request.user.email}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        email = user.email
        logger.info(f"Deleting account for user: {email}")
        user.delete()
        return Response({"message": f"Account for {email} deleted successfully."}, status=status.HTTP_200_OK)
from rest_framework_simplejwt.tokens import RefreshToken

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'is_staff': user.is_staff,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom login serializer that includes is_staff in the response."""
    def validate(self, attrs):
        data = super().validate(attrs)
        data['is_staff'] = self.user.is_staff
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'name': self.user.name,
            'is_staff': self.user.is_staff,
        }
        return data

class AdminTokenObtainPairSerializer(CustomTokenObtainPairSerializer):
    """Admin-only login serializer that enforces is_staff check."""
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_staff:
            from rest_framework import serializers
            raise serializers.ValidationError({"detail": "NOT ELIGIBLE"})
        return data

class CustomTokenObtainPairView(BaseTokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class AdminLoginView(CustomTokenObtainPairView):
    """Explicit admin login view. Enforces staff check and restricted access."""
    serializer_class = AdminTokenObtainPairSerializer

class UserProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        progress, created = UserProgress.objects.get_or_create(user=request.user)
        serializer = UserProgressSerializer(progress)
        return Response(serializer.data)

    def put(self, request):
        progress, created = UserProgress.objects.get_or_create(user=request.user)
        serializer = UserProgressSerializer(progress, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GoalDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        details, created = GoalDetails.objects.get_or_create(user=request.user)
        serializer = GoalDetailsSerializer(details)
        return Response(serializer.data)

    def put(self, request):
        details, created = GoalDetails.objects.get_or_create(user=request.user)
        serializer = GoalDetailsSerializer(details, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReadingAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        analytics, created = ReadingAnalytics.objects.get_or_create(user=request.user)
        serializer = ReadingAnalyticsSerializer(analytics)
        return Response(serializer.data)

    def put(self, request):
        analytics, created = ReadingAnalytics.objects.get_or_create(user=request.user)
        serializer = ReadingAnalyticsSerializer(analytics, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SavedQuotesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quotes = SavedQuote.objects.filter(user=request.user).order_by('-date_saved')
        serializer = SavedQuoteSerializer(quotes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SavedQuoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            # Auto-increment total_quotes_saved in UserProgress
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            progress.total_quotes_saved += 1
            progress.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SavedQuoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, quote_id):
        try:
            quote = SavedQuote.objects.get(id=quote_id, user=request.user)
            quote.delete()
            
            # Decrement total_quotes_saved in UserProgress
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            if progress.total_quotes_saved > 0:
                progress.total_quotes_saved -= 1
                progress.save()
                
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SavedQuote.DoesNotExist:
            return Response({"error": "Quote not found"}, status=status.HTTP_404_NOT_FOUND)

from django.utils import timezone
from .models import DailyBoost, UserBadge, JournalEntry
from .serializers import DailyBoostSerializer, UserBadgeSerializer, JournalEntrySerializer

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress, _ = UserProgress.objects.get_or_create(user=user)
        
        # Fetch books from database by category
        top_books = Book.objects.filter(category='TOP')[:5]
        month_books = Book.objects.filter(category='MONTH')[:5]
        trending_books = Book.objects.filter(category='TRENDING')[:5]
        recommended_book = Book.objects.filter(category='RECOMMENDED').first()

        # If no books in DB, return empty lists
        top_books_data = [{"id": b.id, "title": b.title, "author": b.author, "coverUrl": b.cover_url} for b in top_books]
        month_books_data = [{"id": b.id, "title": b.title, "author": b.author, "coverUrl": b.cover_url} for b in month_books]
        trending_books_data = [{"id": b.id, "title": b.title, "author": b.author, "coverUrl": b.cover_url} for b in trending_books]

        recommended_data = {
            "title": recommended_book.title if recommended_book else "Mindset",
            "description": recommended_book.description if recommended_book else "Based on your interest in growth and habits.",
            "sparkleIcon": "✨"
        }

        # Handle current book null case
        current_book_data = None
        if progress.current_book_title:
            # Try to find the book ID and chapter info based on title
            book_obj = Book.objects.filter(title=progress.current_book_title).first()
            total_chapters = 0
            current_chapter = 1
            if book_obj:
                total_chapters = book_obj.chapters.count()
                # Estimate current chapter from progress
                if total_chapters > 0:
                    current_chapter = max(1, int(progress.current_book_progress * total_chapters))
            current_book_data = {
                "id": book_obj.id if book_obj else 1,
                "title": progress.current_book_title,
                "author": progress.current_book_author,
                "progress": progress.current_book_progress,
                "isPremium": progress.current_book_is_premium,
                "currentChapter": current_chapter,
                "totalChapters": total_chapters
            }

        # Fetch user badges
        badges = UserBadge.objects.filter(user=user).order_by('-date_earned')[:3]
        badges_serializer = UserBadgeSerializer(badges, many=True)

        # Fetch user daily boost
        today = timezone.now().date()
        boost = DailyBoost.objects.filter(user=user, date=today).first()
        if not boost:
            # Fallback if not generated yet - should ideally be generated via DailyBoostView logic
            # for now we'll just return null or a skeleton
            pass

        daily_boost_data = None
        if boost:
            daily_boost_data = DailyBoostSerializer(boost).data

        dashboard_data = {
            "date": timezone.now().strftime("%A, %B %d"),
            "userName": user.name,
            "streakDays": progress.current_streak,
            "goalTitle": progress.active_goal_title,
            "goalSubtitle": progress.active_goal_subtitle or f"Read {progress.active_goal_total_books} {progress.active_goal_unit } This Year",
            "goalType": progress.active_goal_type,
            "goalUnit": progress.active_goal_unit,
            "goalBooksRead": progress.active_goal_books_completed,
            "goalTotalBooks": progress.active_goal_total_books,
            "total_notes_taken": progress.total_notes_taken,
            "currentBook": current_book_data,
            "daily_boost": daily_boost_data,
            "topBooks": top_books_data,
            "monthBooks": month_books_data,
            "trendingBooks": trending_books_data,
            "communityInspiration": {
                "avatarUrls": [],
                "message": "Start reading to see community activity"
            },
            "aiRecommendation": recommended_data,
            "badges": badges_serializer.data,
            "unreadNotificationCount": Notification.objects.filter(user=user, is_read=False).count()
        }
        return Response(dashboard_data)

class NotificationSettingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings, _ = NotificationSetting.objects.get_or_create(user=request.user)
        serializer = NotificationSettingSerializer(settings)
        return Response(serializer.data)

    def post(self, request):
        settings, _ = NotificationSetting.objects.get_or_create(user=request.user)
        serializer = NotificationSettingSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeviceTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_token = request.data.get('device_token')
        if not device_token:
            return Response({"error": "device_token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        token_obj, created = DeviceToken.objects.update_or_create(
            device_token=device_token,
            defaults={'user': request.user}
        )
        return Response({"status": "success", "device_token": device_token}, status=status.HTTP_201_CREATED)

class HomeFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = FeedPost.objects.all().order_by('-date_created')
        serializer = FeedPostSerializer(posts, many=True)
        return Response(serializer.data)

class DailyBoostView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        today = timezone.now().date()
        boost = DailyBoost.objects.filter(user=request.user, date=today).first()
        
        if not boost:
            # Pick a quote based on user interests/goals
            prefs, _ = ReadingPreference.objects.get_or_create(user=request.user)
            
            categories = set()
            if prefs.interests:
                for interest in prefs.interests.split(','):
                    it = interest.strip()
                    if it in INTEREST_MAP:
                        categories.update(INTEREST_MAP[it])
            
            if prefs.improvement_goals:
                for goal in prefs.improvement_goals.split(','):
                    gt = goal.strip()
                    if gt in GOAL_MAP:
                        categories.update(GOAL_MAP[gt])
            
            # If no matches or no preferences, pick from all
            if not categories:
                cat_list = list(QUOTES_DATA.keys())
            else:
                cat_list = list(categories)
            
            # Select random category and random quote from it
            category = random.choice(cat_list)
            quote = random.choice(QUOTES_DATA[category])
            
            # Create the boost for today
            boost = DailyBoost.objects.create(
                user=request.user,
                date=today,
                insight_title=f"Today's {category} Insight",
                quote_text=f'"{quote["text"]}"',
                quote_author=quote["author"],
                article_title=f"The Power of {category}",
                article_preview=f"Exploring how {category.lower()} impacts your daily growth and mindset.",
                ai_reflection=f"Focusing on {category.lower()} today will help you overcome challenges and stay aligned with your goals."
            )
        
        serializer = DailyBoostSerializer(boost)
        return Response(serializer.data)


class UserBadgesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress, _ = UserProgress.objects.get_or_create(user=user)
        goal_details, _ = GoalDetails.objects.get_or_create(user=user)
        
        # Define badges and their logic
        badges_definitions = [
            {
                "id": "streak_14",
                "title": "14-Day Streak",
                "description": "Read for 14 consecutive days",
                "target": 14,
                "current": progress.current_streak,
                "icon": "LocalFireDepartment",
                "tint": "Orange",
                "bgTint": "LightOrange"
            },
            {
                "id": "books_5",
                "title": "5 Books",
                "description": "Complete 5 books",
                "target": 5,
                "current": progress.total_books_read,
                "icon": "MenuBook",
                "tint": "Primary",
                "bgTint": "LightBlue"
            },
            {
                "id": "quotes_30",
                "title": "30 Quotes",
                "description": "Save 30 inspiring quotes",
                "target": 30,
                "current": progress.total_quotes_saved,
                "icon": "FormatQuote",
                "tint": "Purple",
                "bgTint": "LightPurple"
            },
            {
                "id": "highlights_100",
                "title": "100 Highlights",
                "description": "Highlight 100 passages",
                "target": 100,
                "current": progress.total_highlights_made,
                "icon": "EditNote",
                "tint": "Primary",
                "bgTint": "LightBlue"
            },
            {
                "id": "streak_7",
                "title": "7-Day Reader",
                "description": "Read every day for a week",
                "target": 7,
                "current": progress.current_streak,
                "icon": "MilitaryTech",
                "tint": "Green",
                "bgTint": "LightGreen"
            },
            {
                "id": "action_plans_3",
                "title": "Growth Master",
                "description": "Complete 3 Action Plans",
                "target": 3,
                "current": goal_details.challenges_done,
                "icon": "Star",
                "tint": "Yellow",
                "bgTint": "LightYellow"
            }
        ]

        # Calculate progress and unlocked status
        response_data = []
        for b in badges_definitions:
            unlocked = int(b["current"]) >= int(b["target"])
            progress_val = min(1.0, float(b["current"]) / float(b["target"]))
            
            response_data.append({
                "id": b["id"],
                "title": b["title"],
                "description": b["description"],
                "icon_name": b["icon"],
                "tint_color": b["tint"],
                "bg_color": b["bgTint"],
                "unlocked": unlocked,
                "progress": progress_val,
                "current_value": b["current"],
                "target_value": b["target"]
            })

        return Response(response_data)

DAILY_PROMPTS = [
    "What is one small step you took today that brought you closer to your goal?",
    "What book insight changed how you think this week?",
    "What are you grateful for in your reading journey today?",
    "Describe a challenge you overcame today and what you learned.",
    "What habit are you building and how is it going?",
    "What's one quote that resonated with you recently and why?",
    "What would you tell your past self about the knowledge you have now?",
    "How did today's reading session make you feel? Describe the experience.",
    "What is one thing you want to apply from your reading this week?",
    "What fear did you face today, however small?",
    "Describe a moment today where you felt in flow or deeply focused.",
    "What did you learn about yourself from what you read today?",
    "What is one mindset shift you've experienced recently?",
    "How are you investing in yourself differently than a year ago?",
    "What is the most important lesson from your current book?",
]

class JournalEntryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entries = JournalEntry.objects.filter(user=request.user).order_by('-date_created')
        serializer = JournalEntrySerializer(entries, many=True)
        # Pick a daily prompt based on day-of-year for consistency
        from datetime import date
        day_of_year = date.today().timetuple().tm_yday
        today_prompt = DAILY_PROMPTS[day_of_year % len(DAILY_PROMPTS)]
        return Response({
            "entries": serializer.data,
            "today_prompt": today_prompt,
            "today_date": date.today().strftime("%b %d")
        })

    def post(self, request):
        data = request.data.copy()
        # Auto-fill title if not provided
        if not data.get('title'):
            data['title'] = 'Daily Reflection'
        serializer = JournalEntrySerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            # Increment total_notes_taken in UserProgress
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            progress.total_notes_taken += 1
            progress.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChallengeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        challenges = Challenge.objects.filter(is_active=True)
        # Check completion status for current user
        data = []
        for c in challenges:
            uc = UserChallenge.objects.filter(user=request.user, challenge=c).first()
            data.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "reward_xp": c.reward_xp,
                "is_completed": uc.is_completed if uc else False
            })
        return Response(data)

class ChallengeUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, challenge_id):
        challenge = Challenge.objects.get(id=challenge_id)
        uc, created = UserChallenge.objects.get_or_create(user=request.user, challenge=challenge)
        uc.is_completed = request.data.get('is_completed', uc.is_completed)
        if uc.is_completed and not uc.date_completed:
            uc.date_completed = timezone.now().date()
        uc.save()
        return Response({"status": "success", "is_completed": uc.is_completed})

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Mark all as read
        Notification.objects.filter(user=request.user).update(is_read=True)
        return Response({"status": "success"})

class LibraryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all query parameters
        category = request.query_params.get('category')
        sort = request.query_params.get('sort', 'All')
        author = request.query_params.get('author')
        year_min = request.query_params.get('year_min')
        year_max = request.query_params.get('year_max')
        rating = request.query_params.get('rating')
        language = request.query_params.get('language')
        tags = request.query_params.get('tags') # Comma separated
        recently_added = request.query_params.get('recently_added') # 'true' or 'false'
        
        books = Book.objects.all()
        
        # Apply filters
        if category:
            books = books.filter(category__icontains=category)
        if author:
            books = books.filter(author__icontains=author)
        if year_min:
            books = books.filter(year__gte=year_min)
        if year_max:
            books = books.filter(year__lte=year_max)
        if rating:
            books = books.filter(rating__gte=rating)
        if language:
            books = books.filter(language__iexact=language)
        if tags:
            tag_list = tags.split(',')
            for tag in tag_list:
                books = books.filter(tags__icontains=tag.strip())
        
        # Sorting and Recently Added
        if recently_added == 'true' or sort == 'Newest':
            books = books.order_by('-id') # Assuming high ID = newer
        elif sort == 'Most Popular':
            books = books.order_by('-rating') # Use rating as proxy for popularity
        elif sort == 'Highest Rated':
            books = books.order_by('-rating')
        elif sort == 'Most Highlighted':
            # Placeholder for future logic
            books = books.order_by('?')
            
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

class CompletedBooksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_books = UserBook.objects.filter(user=request.user, status='COMPLETED').order_by('-date_completed')
        serializer = UserBookSerializer(user_books, many=True)
        return Response(serializer.data)


class AICoachInsightView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # Get user's current book for personalized insight
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            current_book = progress.current_book_title or "Atomic Habits"
            current_author = progress.current_book_author or "James Clear"
            
            prompt = f"""You are a personal reading coach. Generate a concise insight about the book "{current_book}" by {current_author}.
            
            Return ONLY a JSON object in this exact format (no markdown, no code fences):
            {{"observation": "1 observation", "bookTitle": "{current_book}", "insightText": "1 insight", "actionSteps": [{{"title": "Step 1", "subtitle": "title", "desc": "desc"}}, {{"title": "Step 2", "subtitle": "title", "desc": "desc"}}, {{"title": "Step 3", "subtitle": "title", "desc": "desc"}}]}}"""
            
            response = model.generate_content(prompt)
            
            text = response.text.strip()
            # Clean JSON string
            if text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text[3:]
                if text.endswith('```'):
                    text = text[:-3]
                text = text.strip()
                if text.lower().startswith('json'):
                    text = text[4:].strip()
            
            data = json.loads(text)
            return Response(data)
        except Exception as e:
            logger.error(f"Error in AICoachInsightView: {str(e)}")
            # Fallback to static response
            current_book = "Atomic Habits" # Default if not found
            return Response({
                "observation": "Keep reading to unlock personalized AI insights!",
                "bookTitle": current_book,
                "insightText": "Every page you read brings you closer to your best self.",
                "actionSteps": [
                    {"title": "Step 1", "subtitle": "Read 10 Pages Today", "desc": "Start small and build consistency."},
                    {"title": "Step 2", "subtitle": "Take a Note", "desc": "Write down one thing that resonated with you."},
                    {"title": "Step 3", "subtitle": "Share with a Friend", "desc": "Discuss what you learned to deepen understanding."}
                ]
            })


class AICoachChatView(APIView):
    """Handles conversational AI queries scoped to books/reading/motivation."""
    permission_classes = [IsAuthenticated]

    SYSTEM_PROMPT = """You are a personal reading coach and book advisor for a book reading motivation app. 
    You ONLY answer questions related to: books, reading habits, book recommendations, book summaries, 
    motivation, personal growth, self-improvement through reading, reading strategies, and book-related topics.
    
    If the user asks about anything unrelated to books or reading (like coding, cooking, politics, etc.), 
    politely say: "I'm your reading coach! I can help with book recommendations, reading strategies, and 
    personal growth through books. What would you like to know about reading?"
    
    Keep responses concise (2-4 sentences max unless asked for detail). Be warm, encouraging, and motivational."""

    def post(self, request):
        user_query = request.data.get('query', '')
        if not user_query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # Get context about user's reading
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            current_book = progress.current_book_title or "No book currently"
            
            full_prompt = f"""{self.SYSTEM_PROMPT}

User's current book: {current_book}
User's reading streak: {progress.current_streak} days
Books read: {progress.total_books_read}

User's question: {user_query}"""
            
            response = model.generate_content(full_prompt)
            return Response({
                "query": user_query,
                "response": response.text.strip(),
                "currentBook": current_book
            })
        except Exception as e:
            logger.error(f"Error in AICoachChatView: {str(e)}")
            return Response({
                "query": user_query,
                "response": "I'm having trouble connecting right now. Try asking me about book recommendations, reading habits, or personal growth!",
                "currentBook": current_book
            })


class AICoachStrategyView(APIView):
    """Generates a personalized 30-day reading strategy."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # Get user context
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            current_book = progress.current_book_title or "any motivational book"
            goal_title = progress.active_goal_title or "Read more books"
            books_read = progress.total_books_read
            
            prompt = f"""You are a reading coach. Create a personalized 30-day reading strategy.

User context:
- Currently reading: {current_book}
- Goal: {goal_title}
- Books completed: {books_read}
- Current streak: {progress.current_streak} days

Return ONLY a JSON object (no markdown, no code fences) with this format:
{{"title": "Your 30-Day Strategy Title", "description": "Brief motivational description", "weeks": [{{"week": 1, "title": "Week 1 Title", "tasks": ["Task 1", "Task 2", "Task 3"]}}, {{"week": 2, "title": "Week 2 Title", "tasks": ["Task 1", "Task 2", "Task 3"]}}, {{"week": 3, "title": "Week 3 Title", "tasks": ["Task 1", "Task 2", "Task 3"]}}, {{"week": 4, "title": "Week 4 Title", "tasks": ["Task 1", "Task 2", "Task 3"]}}]}}"""
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            # Clean JSON string
            if text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text[3:]
                if text.endswith('```'):
                    text = text[:-3]
                text = text.strip()
                if text.lower().startswith('json'):
                    text = text[4:].strip()
            
            data = json.loads(text)
            return Response(data)
        except Exception as e:
            logger.error(f"Error in AICoachStrategyView: {str(e)}")
            return Response({
                "title": "30-Day Reading Challenge",
                "description": "Build a consistent reading habit in 30 days!",
                "weeks": [
                    {"week": 1, "title": "Build the Foundation", "tasks": ["Read 10 pages daily", "Set a fixed reading time", "Create a reading nook"]},
                    {"week": 2, "title": "Deepen the Habit", "tasks": ["Increase to 20 pages", "Take notes while reading", "Share one insight daily"]},
                    {"week": 3, "title": "Challenge Yourself", "tasks": ["Try a new genre", "Read for 30 minutes daily", "Write a mini book review"]},
                    {"week": 4, "title": "Cement the Lifestyle", "tasks": ["Complete your current book", "Start a new book", "Reflect on your growth"]}
                ]
            })

class AISummaryView(APIView):
    """Generates a concise 2-line summary of the provided content."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        content = request.data.get('content', '')
        if not content:
            return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            prompt = f"""Summarize the following book content in EXACTLY 2 lines. 
            Keep it motivational and insightful.
            
            Content:
            {content[:4000]}
            
            Return ONLY the 2-line summary."""
            
            response = model.generate_content(prompt)
            summary = response.text.strip()
            
            return Response({
                "summary": summary
            })
        except Exception as e:
            logger.error(f"Error in AISummaryView: {str(e)}")
            return Response({
                "summary": "Focus on the core message and reflect on how you can apply it today. Every page holds a new opportunity for growth."
            })

class TranslateView(APIView):
    """Translates text to a target language using Gemini (fallback for web since ML Kit is mobile only)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '')
        target_lang = request.data.get('target_language', 'es') # e.g., 'es', 'fr', 'ta'
        
        if not text:
            return Response({"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            prompt = f"Translate the following text to {target_lang}. Return ONLY the translated text, nothing else.\n\nText: {text}"
            response = model.generate_content(prompt)
            return Response({"translated_text": response.text.strip()})
        except Exception as e:
            logger.error(f"Error in TranslateView: {str(e)}")
            return Response({"translated_text": "[Translation Error: Service Unavailable]"})


class ChapterListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, book_id):
        chapters = Chapter.objects.filter(book_id=book_id).order_by('order')
        serializer = ChapterSerializer(chapters, many=True)
        return Response(serializer.data)

from datetime import timedelta

class TrackBookOpenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        book_id = request.data.get('book_id')
        book_title = request.data.get('title', '')
        book_author = request.data.get('author', '')
        is_premium = request.data.get('is_premium', False)

        user = request.user
        progress, _ = UserProgress.objects.get_or_create(user=user)
        today = timezone.now().date()

        # --- Streak Logic ---
        if progress.last_active_date:
            delta = (today - progress.last_active_date).days
            if delta == 1:
                progress.current_streak += 1
            elif delta > 1:
                progress.current_streak = 1  # Reset streak
            # delta == 0 means same day, no change
        else:
            progress.current_streak = 1  # First ever open

        progress.last_active_date = today

        # --- Update current book ---
        progress.current_book_title = book_title
        progress.current_book_author = book_author
        progress.current_book_is_premium = is_premium
        progress.save()

        # --- Create/Update UserBook record ---
        if book_id:
            try:
                book = Book.objects.get(id=book_id)
                UserBook.objects.get_or_create(user=user, book=book)
            except Book.DoesNotExist:
                pass

        return Response({
            'current_streak': progress.current_streak,
            'current_book_title': progress.current_book_title
        })

class BookDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
            serializer = BookSerializer(book)
            return Response(serializer.data)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

class UpdateReadingProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        minutes = request.data.get('minutes', 0)
        pages = request.data.get('pages', 0)
        book_id = request.data.get('book_id')

        user = request.user
        progress, _ = UserProgress.objects.get_or_create(user=user)
        analytics, _ = ReadingAnalytics.objects.get_or_create(user=user)

        # Update total hours (convert minutes added)
        # We'll store internal minutes if we want precision, but for now we update total_hours_read
        # Let's say we update total_hours_read every 60 accumulated minutes
        # or just add minutes and calculate hours in the view.
        # Actually, let's keep it simple: total_hours_read is a counter.
        # If the frontend sends minutes, we can add to a 'total_minutes' field or just convert.
        
        # Adding a temporary 'minutes_accumulator' or just using daily_average_minutes
        analytics.daily_average_minutes += minutes
        analytics.pages_read += pages
        analytics.save()

        # Update total hours in progress if minutes cross a threshold
        new_total_hours = analytics.daily_average_minutes // 60
        if new_total_hours > progress.total_hours_read:
            progress.total_hours_read = new_total_hours
            progress.save()

        # Update UserBook time spent
        if book_id:
            user_book = UserBook.objects.filter(user=user, book_id=book_id).first()
            if user_book:
                user_book.time_spent_minutes += minutes
                user_book.save()

        return Response({
            "total_hours": progress.total_hours_read,
            "pages_read": analytics.pages_read,
            "minutes_today": analytics.daily_average_minutes
        })


class MoodGraphView(APIView):
    """Computes mood graph data from last 7 journal entries.
    Mood mapping: rough=1.5, okay=3.0, great=4.5
    Returns daily mood values for the Mood Elevation graph."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        mood_map = {'rough': 1.5, 'okay': 3.0, 'great': 4.5}
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        # Get journal entries from the last 7 days
        week_start = today - timedelta(days=today.weekday())  # Monday
        entries = JournalEntry.objects.filter(
            user=request.user,
            date_created__gte=week_start,
            date_created__lte=week_start + timedelta(days=6)
        ).order_by('date_created')

        # Build a dict of day_index -> mood value
        daily_moods = {}
        for entry in entries:
            day_idx = entry.date_created.weekday()  # 0=Mon, 6=Sun
            daily_moods[day_idx] = mood_map.get(entry.mood, 3.0)

        # Build the response: 7 values (Mon-Sun), default 2.5 if no entry
        mood_values = [daily_moods.get(i, 2.5) for i in range(7)]

        return Response({
            'mood_values': mood_values,
            'days': day_names,
            'has_data': len(daily_moods) > 0
        })


# ==================== Forgot Password OTP Views ====================

import requests as http_requests
from .models import PasswordResetOTP, LoginOTP

class ForgotPasswordView(APIView):
    """Send a 6-digit OTP to the user's email via Brevo."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'No account found with this email.'}, status=status.HTTP_404_NOT_FOUND)

        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))

        # Invalidate any previous unused OTPs for this user
        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)

        # Save new OTP
        PasswordResetOTP.objects.create(user=user, otp=otp_code)

        # Send OTP via Gmail SMTP
        try:
            subject = "MotivBooks - Password Reset OTP"
            message = f"Hi {user.name}, your OTP for password reset is: {otp_code}\n\nThis OTP is valid for 10 minutes."
            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 12px;">
                    <h1 style="color: #e0e0e0; margin-bottom: 5px;">📚✨ MotivBooks</h1>
                    <p style="color: #8ecae6;">Read. Grow. Become.</p>
                </div>
                <div style="padding: 30px 20px; text-align: center;">
                    <h2 style="color: #333;">Password Reset</h2>
                    <p style="color: #666; font-size: 16px;">Hi {user.name}, use the OTP below to reset your password:</p>
                    <div style="background: #f0f7ff; border: 2px dashed #4cc9f0; border-radius: 10px; padding: 20px; margin: 20px 0;">
                        <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1a1a2e;">{otp_code}</span>
                    </div>
                    <p style="color: #999; font-size: 14px;">This OTP is valid for <strong>10 minutes</strong>. Do not share it with anyone.</p>
                </div>
            </div>
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Error sending OTP email: {str(e)}")
            return Response({'error': 'Failed to send OTP email. Please check your internet connection or email configuration.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'OTP sent to your email successfully.'})


class VerifyOTPView(APIView):
    """Verify a 6-digit OTP."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        otp_code = request.data.get('otp', '').strip()

        if not email or not otp_code:
            return Response({'error': 'Email and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email.'}, status=status.HTTP_404_NOT_FOUND)

        # Find the latest unused OTP for this user
        otp_entry = PasswordResetOTP.objects.filter(
            user=user, otp=otp_code, is_used=False
        ).order_by('-created_at').first()

        if not otp_entry:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check expiry (10 minutes)
        from django.utils import timezone as tz
        elapsed = (tz.now() - otp_entry.created_at).total_seconds()
        if elapsed > 600:  # 10 minutes
            return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP verified successfully.'})


class ResetPasswordView(APIView):
    """Reset user password after OTP verification."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        otp_code = request.data.get('otp', '').strip()
        new_password = request.data.get('new_password', '')

        if not email or not otp_code or not new_password:
            return Response({'error': 'Email, OTP, and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        from .utils import validate_password_strength
        is_strong, msg = validate_password_strength(new_password)
        if not is_strong:
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email.'}, status=status.HTTP_404_NOT_FOUND)

        # Re-verify OTP
        otp_entry = PasswordResetOTP.objects.filter(
            user=user, otp=otp_code, is_used=False
        ).order_by('-created_at').first()

        if not otp_entry:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.utils import timezone as tz
        elapsed = (tz.now() - otp_entry.created_at).total_seconds()
        if elapsed > 600:
            return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        # Set new password and mark OTP as used
        user.set_password(new_password)
        user.save()
        otp_entry.is_used = True
        otp_entry.save()

        return Response({'message': 'Password reset successfully. Please login with your new password.'})


class ChangePasswordView(APIView):
    """Change user password for authenticated users."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
             return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
             return Response({"error": "New passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(old_password):
             return Response({"error": "Incorrect current password"}, status=status.HTTP_400_BAD_REQUEST)

        from .utils import validate_password_strength
        is_strong, msg = validate_password_strength(new_password)
        if not is_strong:
             return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        return Response({"message": "Password updated successfully"})


# ==================== Login OTP Views ====================

class SendLoginOTPView(APIView):
    """Send a 6-digit OTP to the user's email for login."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'No account found with this email.'}, status=status.HTTP_404_NOT_FOUND)

        otp_code = str(random.randint(100000, 999999))
        LoginOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        LoginOTP.objects.create(user=user, otp=otp_code)

        try:
            subject = "MotivBooks - Login OTP"
            message = f"Hi {user.name}, your login OTP is: {otp_code}\n\nThis OTP is valid for 10 minutes."
            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 12px;">
                    <h1 style="color: #e0e0e0; margin-bottom: 5px;">📚✨ MotivBooks</h1>
                    <p style="color: #8ecae6;">Read. Grow. Become.</p>
                </div>
                <div style="padding: 30px 20px; text-align: center;">
                    <h2 style="color: #333;">Login Verification</h2>
                    <p style="color: #666; font-size: 16px;">Hi {user.name}, use the OTP below to sign into your account:</p>
                    <div style="background: #f0f7ff; border: 2px dashed #4cc9f0; border-radius: 10px; padding: 20px; margin: 20px 0;">
                        <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1a1a2e;">{otp_code}</span>
                    </div>
                    <p style="color: #999; font-size: 14px;">This OTP is valid for <strong>10 minutes</strong>.</p>
                </div>
            </div>
            """
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message)
        except Exception as e:
            logger.error(f"Error sending login OTP: {str(e)}")
            return Response({'error': 'Failed to send OTP.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'Login OTP sent successfully.'})

class LoginWithOTPView(APIView):
    """Verify login OTP and return JWT tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        otp_code = request.data.get('otp', '').strip()

        if not email or not otp_code:
            return Response({'error': 'Email and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email.'}, status=status.HTTP_404_NOT_FOUND)

        otp_entry = LoginOTP.objects.filter(user=user, otp=otp_code, is_used=False).order_by('-created_at').first()

        if not otp_entry:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.utils import timezone as tz
        if (tz.now() - otp_entry.created_at).total_seconds() > 600:
            return Response({'error': 'OTP expired.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_entry.is_used = True
        otp_entry.save()

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            },
            'is_staff': user.is_staff
        })


# ==================== Admin Book Management Views ====================

from .serializers import AdminBookUploadSerializer, AdminChapterSerializer

class AdminBookListCreateView(APIView):
    """Admin-only: List all books or create a new book."""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        books = Book.objects.all().order_by('-id')
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AdminBookUploadSerializer(data=request.data)
        if serializer.is_valid():
            book = serializer.save()
            
            # If PDF is uploaded, try to extract text and create a chapter
            if 'pdf_file' in request.FILES:
                pdf_file = request.FILES['pdf_file']
                try:
                    import PyPDF2
                    import io
                    
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
                    full_text = ""
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n\n"
                    
                    if full_text.strip():
                        # Create a default chapter with the extracted text
                        Chapter.objects.create(
                            book=book,
                            title="Full Book Content",
                            content=full_text,
                            order=1
                        )
                        logger.info(f"Automatically created chapter for book: {book.title} from PDF.")
                except Exception as e:
                    logger.error(f"Failed to extract text from PDF for book {book.id}: {str(e)}")
            
            return Response(AdminBookUploadSerializer(book).data, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"AdminBookUpload validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBookDeleteView(APIView):
    """Admin-only: Delete a book."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, book_id):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            book = Book.objects.get(id=book_id)
            book.delete()
            return Response({'message': 'Book deleted successfully.'}, status=status.HTTP_200_OK)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)


class AdminChapterListCreateView(APIView):
    """Admin-only: List chapters for a book or add a new chapter."""
    permission_classes = [IsAuthenticated]

    def get(self, request, book_id):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        chapters = Chapter.objects.filter(book=book).order_by('order')
        serializer = AdminChapterSerializer(chapters, many=True)
        return Response(serializer.data)

    def post(self, request, book_id):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminChapterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(book=book)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
