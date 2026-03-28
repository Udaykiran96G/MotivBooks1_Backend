from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email).lower().strip()
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        return self.get(email__iexact=username)

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    current_streak = models.IntegerField(default=0)
    active_goal_title = models.CharField(max_length=255, default='Set a Goal', blank=True)
    active_goal_subtitle = models.CharField(max_length=255, default='', blank=True)
    active_goal_type = models.CharField(max_length=50, default='BOOKS', blank=True) # e.g., 'BOOKS', 'MINUTES'
    active_goal_unit = models.CharField(max_length=20, default='books', blank=True) # e.g., 'books', 'mins'
    active_goal_books_completed = models.IntegerField(default=0)
    active_goal_total_books = models.IntegerField(default=1)
    total_books_read = models.IntegerField(default=0)
    total_hours_read = models.IntegerField(default=0)
    total_quotes_saved = models.IntegerField(default=0)
    total_highlights_made = models.IntegerField(default=0)
    total_notes_taken = models.IntegerField(default=0)
    mood_before_reading = models.CharField(max_length=255, default='2.5,2.5,2.0,2.8,3.2,3.2')
    mood_after_reading = models.CharField(max_length=255, default='3.2,3.5,2.8,4.0,4.2,3.8')
    weekly_digest_text = models.TextField(blank=True, default='')
    weekly_digest_date_range = models.CharField(max_length=50, blank=True, default='')
    
    last_active_date = models.DateField(null=True, blank=True)
    current_book_title = models.CharField(max_length=255, blank=True, null=True)
    current_book_author = models.CharField(max_length=255, blank=True, null=True)
    current_book_progress = models.FloatField(default=0.0)
    current_book_is_premium = models.BooleanField(default=False)

    def __str__(self):
        return f"Progress for {self.user.email}"

class GoalDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='goal_details')
    deadline = models.DateField(null=True, blank=True)
    reflections_written = models.IntegerField(default=0)
    challenges_done = models.IntegerField(default=0)

    def __str__(self):
        return f"Goal Details for {self.user.email}"

class ReadingAnalytics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reading_analytics')
    weekly_improvement_percentage = models.IntegerField(default=0)
    daily_average_minutes = models.IntegerField(default=0)
    longest_session_minutes = models.IntegerField(default=0)
    pages_read = models.IntegerField(default=0)
    mon_progress = models.FloatField(default=0.0)
    tue_progress = models.FloatField(default=0.0)
    wed_progress = models.FloatField(default=0.0)
    thu_progress = models.FloatField(default=0.0)
    fri_progress = models.FloatField(default=0.0)
    sat_progress = models.FloatField(default=0.0)
    sun_progress = models.FloatField(default=0.0)

    def __str__(self):
        return f"Reading Analytics for {self.user.email}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    member_since = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Profile for {self.user.email}"

class ReadingPreference(models.Model):
    THEME_CHOICES = [
        ('Light', 'Light'),
        ('Sepia', 'Sepia'),
        ('Dark', 'Dark'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    font_size = models.IntegerField(default=16)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='Light')
    language = models.CharField(max_length=50, default='English')
    auto_save_highlights = models.BooleanField(default=True)
    
    # Onboarding choices
    interests = models.TextField(blank=True, default='') # Comma-separated strings
    improvement_goals = models.TextField(blank=True, default='') # Comma-separated strings
    reading_style = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"Preferences for {self.user.email}"

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('Free', 'Free'),
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Expired', 'Expired'),
        ('Cancelled', 'Cancelled'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='Free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    expiry_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.plan_type} Subscription for {self.user.email}"

class SavedQuote(models.Model):
# ... (rest of the file stays same, but I need to make sure I don't delete anything)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_quotes')
    quote = models.TextField()
    author = models.CharField(max_length=255)
    book = models.CharField(max_length=255)
    date_saved = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Quote by {self.author} for {self.user.email}"

class DailyBoost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_boosts', null=True, blank=True)
    date = models.DateField()
    insight_title = models.CharField(max_length=255, default="Find Your Inner Calm")
    quote_text = models.TextField()
    quote_author = models.CharField(max_length=255)
    article_title = models.CharField(max_length=255)
    article_preview = models.TextField()
    ai_reflection = models.TextField()

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Daily Boost for {self.user.email} on {self.date}"

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    title = models.CharField(max_length=255)
    date_earned = models.DateField(auto_now_add=True)
    icon_name = models.CharField(max_length=100) # e.g., 'MenuBook', 'LocalFireDepartment'
    tint_color = models.CharField(max_length=50) # e.g., 'Primary', 'Orange'
    bg_color = models.CharField(max_length=50)   # e.g., 'LightBlue', 'LightOrange'

    def __str__(self):
        return f"{self.title} badge for {self.user.email}"

class JournalEntry(models.Model):
    MOOD_CHOICES = [
        ('rough', 'Rough'),
        ('okay', 'Okay'),
        ('great', 'Great'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    title = models.CharField(max_length=255, blank=True, default='Daily Reflection')
    content = models.TextField()
    mood = models.CharField(max_length=10, choices=MOOD_CHOICES, default='okay')
    prompt = models.TextField(blank=True, default='')
    date_created = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Journal '{self.title}' by {self.user.email}"

class Challenge(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    reward_xp = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class UserChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_challenges')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    date_completed = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.challenge.title}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=50, default='general') # e.g., 'streak', 'challenge', 'goal'
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"

class Book(models.Model):
    CATEGORY_CHOICES = [
        ('TOP', 'Top Books'),
        ('MONTH', 'Books of the Month'),
        ('TRENDING', 'Trending in Motivation'),
        ('RECOMMENDED', 'AI Recommendation'),
    ]
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover_url = models.URLField(max_length=500, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='TRENDING')
    is_premium = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    genre = models.CharField(max_length=255, blank=True, null=True)
    file_url = models.URLField(max_length=500, blank=True, null=True) # Public URL if hosted
    file_path = models.CharField(max_length=500, blank=True, null=True) # Local path on server
    pdf_file = models.FileField(upload_to='books/pdfs/', null=True, blank=True)

    def __str__(self):
        return self.title

class FeedPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_posts', null=True, blank=True) # Null for system/editorial posts
    quote = models.TextField()
    author = models.CharField(max_length=255)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    is_editorial = models.BooleanField(default=False)
    article_title = models.CharField(max_length=255, blank=True, null=True)
    article_preview = models.TextField(blank=True, null=True)
    read_time_minutes = models.IntegerField(default=2)

    def __str__(self):
        return f"Post by {self.author}: {self.quote[:50]}..."

class UserBook(models.Model):
    STATUS_CHOICES = [
        ('READING', 'Reading'),
        ('COMPLETED', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='READING')
    date_completed = models.DateField(null=True, blank=True)
    time_spent_minutes = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.email} - {self.book.title} ({self.status})"

class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']
        unique_together = ('book', 'order')

    def __str__(self):
        return f"{self.book.title} - Chapter {self.order}: {self.title}"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.email} at {self.created_at}"


class NotificationSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    push_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    
    # Specific notification types from the UI
    daily_reading_reminder = models.BooleanField(default=True)
    streak_protection_alert = models.BooleanField(default=True)
    goal_based_reminder = models.BooleanField(default=False)
    weekly_growth_report = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification Settings for {self.user.email}"

class DeviceToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    device_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token for {self.user.email}: {self.device_token[:10]}..."


class LoginOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Login OTP for {self.user.email} at {self.created_at}"

class MindsetKB(models.Model):
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=255, blank=True, null=True)
    emotion = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.question[:50]}..."
