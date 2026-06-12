from django.db import models
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field


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
