import uuid as _uuid
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from django.db.models import Avg


# ── In-App Notifications ──────────────────────────────────────────────────────

class Notification(models.Model):
    NOTIF_TYPES = [
        ('lesson_approved', 'Lesson Approved'),
        ('lesson_rejected', 'Lesson Rejected'),
        ('new_comment', 'New Comment'),
        ('certificate_earned', 'Certificate Earned'),
        ('quiz_passed', 'Quiz Passed'),
        ('topic_proposal_approved', 'Topic Proposal Approved'),
        ('topic_proposal_rejected', 'Topic Proposal Rejected'),
        ('topic_review_submitted', 'Topic Review Submitted'),
        ('topic_published', 'Topic Published'),
        ('topic_changes_requested', 'Topic Changes Requested'),
        ('topic_rejected_to_draft', 'Topic Rejected to Draft'),
    ]
    NOTIF_ICONS = {
        'lesson_approved': 'circle-check',
        'lesson_rejected': 'circle-xmark',
        'new_comment': 'comment',
        'certificate_earned': 'award',
        'quiz_passed': 'trophy',
        'topic_proposal_approved': 'circle-check',
        'topic_proposal_rejected': 'circle-xmark',
        'topic_review_submitted': 'magnifying-glass',
        'topic_published': 'rocket',
        'topic_changes_requested': 'pen-to-square',
        'topic_rejected_to_draft': 'circle-xmark',
    }
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=40, choices=NOTIF_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f'{self.user.username} — {self.title}'

    @property
    def icon(self):
        return self.NOTIF_ICONS.get(self.notif_type, 'bell')

    @classmethod
    def create(cls, user, notif_type, title, message, url=''):
        try:
            return cls.objects.create(
                user=user, notif_type=notif_type,
                title=title, message=message, url=url,
            )
        except Exception:
            pass


# ── Topic Proposals ───────────────────────────────────────────────────────────

PROPOSAL_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending_review', 'Pending Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]


class TopicProposal(models.Model):
    submitted_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='topic_proposals',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(
        help_text='What should this topic cover? Who is the audience?'
    )
    icon_html = models.CharField(
        max_length=300,
        default='<i class="fa-solid fa-book"></i>',
        help_text='Optional HTML icon snippet.',
    )
    status = models.CharField(
        max_length=20, choices=PROPOSAL_STATUS_CHOICES, default='draft',
    )
    rejection_note = models.TextField(blank=True)
    approved_topic = models.OneToOneField(
        'Topic', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='from_proposal',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Topic Proposal'
        verbose_name_plural = 'Topic Proposals'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(status='approved') | models.Q(approved_topic__isnull=False),
                name='topicproposal_approved_requires_topic',
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.status}) — {self.submitted_by.username}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.status == 'approved' and not self.approved_topic_id:
            raise ValidationError(
                {'status': (
                    'Cannot manually set status to "approved". '
                    'Use the Approve action to approve proposals — '
                    'this ensures a Topic is created and ownership is assigned.'
                )}
            )

    def approve(self):
        from django.utils.text import slugify
        from django.urls import reverse
        from django.db import transaction
        with transaction.atomic():
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Topic.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            topic = Topic.objects.create(
                title=self.title, slug=slug, description=self.description,
                icon_html=self.icon_html, is_published=False, order=0,
                owner=self.submitted_by, status='draft',
            )
            self.status = 'approved'
            self.approved_topic = topic
            self.save()
        manage_url = reverse('manage_topic', kwargs={'slug': topic.slug})
        Notification.create(
            user=self.submitted_by,
            notif_type='topic_proposal_approved',
            title=f'Topic proposal "{self.title}" approved!',
            message=(
                f'Your topic proposal "{self.title}" was approved! You are now the topic owner. '
                f'Head to your contributor dashboard to start adding chapters and lessons.'
            ),
            url=manage_url,
        )
        return topic

    def reject(self, note=''):
        self.status = 'rejected'
        self.rejection_note = note
        self.save()
        Notification.create(
            user=self.submitted_by,
            notif_type='topic_proposal_rejected',
            title=f'Topic proposal "{self.title}" needs revision',
            message=note or 'Your topic proposal was not approved at this time. Please revise and resubmit.',
        )


# ── Core Content ──────────────────────────────────────────────────────────────

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
    ('published', 'Published'),
]

TOPIC_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending_review', 'Pending Review'),
    ('changes_requested', 'Changes Requested'),
    ('published', 'Published'),
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
    image_alt = models.CharField(max_length=255, blank=True)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=TOPIC_STATUS_CHOICES, default='draft',
    )
    review_notes = models.TextField(blank=True)
    submitted_for_review_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_topics',
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_topics',
    )
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

    def submit_for_review(self):
        from django.db import transaction
        with transaction.atomic():
            self.status = 'pending_review'
            self.submitted_for_review_at = timezone.now()
            self.review_notes = ''
            self.save(update_fields=['status', 'submitted_for_review_at', 'review_notes', 'updated_at'])

    def publish_topic(self, reviewed_by=None):
        from django.db import transaction
        with transaction.atomic():
            self.status = 'published'
            self.is_published = True
            self.reviewed_at = timezone.now()
            self.review_notes = ''
            if reviewed_by:
                self.reviewed_by = reviewed_by
            self.save()
            self.chapters.update(is_published=True)
            Lesson.objects.filter(chapter__topic=self).update(
                is_published=True, status='published',
            )

    def request_changes(self, notes='', reviewed_by=None):
        from django.db import transaction
        with transaction.atomic():
            self.status = 'changes_requested'
            self.is_published = False
            self.review_notes = notes
            self.reviewed_at = timezone.now()
            if reviewed_by:
                self.reviewed_by = reviewed_by
            self.save()
            self.chapters.update(is_published=False)
            Lesson.objects.filter(chapter__topic=self).update(is_published=False)

    def reject_to_draft(self, notes='', reviewed_by=None):
        from django.db import transaction
        with transaction.atomic():
            self.status = 'draft'
            self.is_published = False
            self.review_notes = notes
            self.reviewed_at = timezone.now()
            if reviewed_by:
                self.reviewed_by = reviewed_by
            self.save()
            self.chapters.update(is_published=False)
            Lesson.objects.filter(chapter__topic=self).update(is_published=False)


class Chapter(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField()
    learning_objectives = CKEditor5Field(blank=True)
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_chapters',
    )
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
    content = CKEditor5Field(blank=True)
    video_url = models.URLField(blank=True)
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='beginner')
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=5)
    required_quiz_questions = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            'Number of random quiz questions required for lesson completion. '
            'Leave empty to allow normal completion. Set a number to require passing a quiz before completion.'
        ),
    )
    is_published = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=LESSON_STATUS_CHOICES, default='draft')
    rejection_note = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
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

    @property
    def avg_rating(self):
        result = self.ratings.aggregate(avg=Avg('rating'))
        val = result['avg']
        return round(val, 1) if val else None

    @property
    def rating_count(self):
        return self.ratings.count()

    @property
    def comment_count(self):
        return self.comments.filter(is_deleted=False).count()

    def publish(self):
        self.status = 'published'
        self.is_published = True
        if not self.published_at:
            self.published_at = timezone.now()
        self.save()

    def reject(self, note=''):
        self.status = 'draft'
        self.is_published = False
        self.rejection_note = note
        self.save()


class UserLessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    progress_pct = models.PositiveIntegerField(default=0)
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


# ── Comments & Discussions ────────────────────────────────────────────────────

class LessonComment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Lesson Comment'
        verbose_name_plural = 'Lesson Comments'

    def __str__(self):
        return f'{self.user.username} on "{self.lesson.title}": {self.content[:60]}'

    @property
    def active_reply_count(self):
        return self.replies.filter(is_deleted=False).count()


class CommentReply(models.Model):
    comment = models.ForeignKey(LessonComment, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comment Reply'
        verbose_name_plural = 'Comment Replies'

    def __str__(self):
        return f'{self.user.username} reply → comment #{self.comment.id}'


# ── Lesson Ratings ────────────────────────────────────────────────────────────

class LessonRating(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_ratings')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('lesson', 'user')
        ordering = ['-created_at']
        verbose_name = 'Lesson Rating'
        verbose_name_plural = 'Lesson Ratings'

    def __str__(self):
        return f'{self.user.username} rated "{self.lesson.title}": {self.rating}/5'


# ── Completion Certificates ───────────────────────────────────────────────────

class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='certificates')
    certificate_id = models.UUIDField(default=_uuid.uuid4, unique=True, editable=False)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'topic')
        ordering = ['-issued_at']
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'

    def __str__(self):
        return f'{self.user.username} — {self.topic.title} Certificate'

    def get_absolute_url(self):
        return reverse('certificate_view', kwargs={'certificate_id': self.certificate_id})

    def get_verify_url(self):
        return reverse('certificate_verify', kwargs={'certificate_id': self.certificate_id})
