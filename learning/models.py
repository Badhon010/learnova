from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone


DIFFICULTY_CHOICES = [
    ('beginner', 'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
]

DIFFICULTY_COLOR = {
    'beginner': 'badge-beginner',
    'intermediate': 'badge-intermediate',
    'advanced': 'badge-advanced',
}

LESSON_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending_review', 'Pending Review'),
    ('published', 'Published'),
    ('rejected', 'Rejected'),
]


class Topic(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField()
    icon_html = models.TextField(
        default='<i class="fa-solid fa-book"></i>',
        help_text=(
            'Full HTML icon. E.g. <code>&lt;i class="fa-brands fa-python"&gt;&lt;/i&gt;</code> '
            'or an inline SVG.'
        ),
    )
    image = models.ImageField(upload_to='topics/', blank=True, null=True)
    image_alt = models.CharField(max_length=255, blank=True, help_text='Alt text for the topic image.')
    meta_title = models.CharField(
        max_length=60, blank=True,
        help_text='SEO page title (max 60 chars). Auto-generated when blank.',
    )
    meta_description = models.CharField(
        max_length=160, blank=True,
        help_text='SEO meta description (max 160 chars). Uses topic description when blank.',
    )
    featured = models.BooleanField(
        default=False,
        help_text='Show in the Featured Topics section on the homepage.',
    )
    order = models.PositiveIntegerField(default=0, help_text='Display order on the topics listing page')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('topic_detail', kwargs={'slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or f'Learn {self.title} — Learnova'

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        desc = self.description
        return desc[:157] + '…' if len(desc) > 157 else desc


class Chapter(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField()
    learning_objectives = CKEditor5Field(
        blank=True,
        help_text='What will learners achieve in this chapter?'
    )
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, default=0.0, help_text='Estimated hours to complete the chapter.')
    meta_title = models.CharField(
        max_length=60, blank=True,
        help_text='SEO page title (max 60 chars). Auto-generated when blank.',
    )
    meta_description = models.CharField(
        max_length=160, blank=True,
        help_text='SEO meta description (max 160 chars). Uses chapter description when blank.',
    )
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return f'{self.topic.title} — {self.title}'

    def get_absolute_url(self):
        return reverse('chapter_detail', kwargs={
            'topic_slug': self.topic.slug,
            'chapter_slug': self.slug,
        })

    def get_meta_title(self):
        return self.meta_title or f'{self.title} — {self.topic.title} | Learnova'

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        desc = self.description
        return desc[:157] + '…' if len(desc) > 157 else desc

    @property
    def lesson_count(self):
        return self.lessons.filter(is_published=True).count()


class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    summary = models.TextField()
    content = CKEditor5Field(
        blank=True,
        help_text=(
            'Full lesson content. Use CKEditor 5 to add headings, images, links, lists, tables, and more.'
        ),
    )
    video_url = models.URLField(
        blank=True,
        help_text='Optional video URL (e.g. YouTube/Vimeo) for the lesson.'
    )
    difficulty = models.CharField(
        max_length=15,
        choices=DIFFICULTY_CHOICES,
        default='beginner',
        help_text='Difficulty level displayed to learners.',
    )
    meta_title = models.CharField(
        max_length=60, blank=True,
        help_text='SEO page title (max 60 chars). Auto-generated when blank.',
    )
    meta_description = models.CharField(
        max_length=160, blank=True,
        help_text='SEO meta description (max 160 chars). Uses lesson summary when blank.',
    )
    featured = models.BooleanField(
        default=False,
        help_text='Show in the Featured / Popular Lessons section on the homepage.',
    )
    order = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=5, help_text='Estimated reading time in minutes')
    is_published = models.BooleanField(default=True)

    # Contributor workflow
    status = models.CharField(
        max_length=20,
        choices=LESSON_STATUS_CHOICES,
        default='published',
        help_text='Lesson publication status.',
    )
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='submitted_lessons',
        help_text='The contributor who submitted this lesson.',
    )
    rejection_note = models.TextField(
        blank=True,
        help_text='Admin note explaining why this lesson was rejected.',
    )
    published_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When the lesson was published.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return f'{self.chapter.topic.title} / {self.chapter.title} / {self.title}'

    def get_absolute_url(self):
        return reverse('lesson_detail', kwargs={'slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or f'{self.title} — {self.chapter.topic.title} | Learnova'

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        s = self.summary
        return s[:157] + '…' if len(s) > 157 else s

    @property
    def difficulty_label(self):
        return dict(DIFFICULTY_CHOICES).get(self.difficulty, self.difficulty.capitalize())

    @property
    def difficulty_class(self):
        return DIFFICULTY_COLOR.get(self.difficulty, 'badge-beginner')

    def publish(self):
        self.status = 'published'
        self.is_published = True
        if not self.published_at:
            self.published_at = timezone.now()
        self.save()

    def reject(self, note=''):
        self.status = 'rejected'
        self.is_published = False
        self.rejection_note = note
        self.save()


class UserLessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    progress_pct = models.PositiveIntegerField(default=0, help_text='Reading progress 0–100%')
    last_viewed = models.DateTimeField(auto_now=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name = 'Lesson Progress'
        verbose_name_plural = 'Lesson Progress'

    def __str__(self):
        return f'{self.user.username} — {self.lesson.title} ({self.progress_pct}%)'


class LessonBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')
        ordering = ['-created_at']
        verbose_name = 'Lesson Bookmark'
        verbose_name_plural = 'Lesson Bookmarks'

    def __str__(self):
        return f'{self.user.username} → {self.lesson.title}'


class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='recent_views')
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')
        ordering = ['-viewed_at']
        verbose_name = 'Recently Viewed'
        verbose_name_plural = 'Recently Viewed'

    def __str__(self):
        return f'{self.user.username} viewed {self.lesson.title}'
