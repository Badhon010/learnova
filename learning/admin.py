from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from unfold.admin import ModelAdmin, TabularInline
from .models import Topic, Chapter, Lesson, UserLessonProgress, LessonBookmark, RecentlyViewed


class ChapterInline(TabularInline):
    model = Chapter
    extra = 1
    fields = ['title', 'slug', 'order', 'is_published']
    prepopulated_fields = {'slug': ('title',)}
    show_change_link = True


class LessonInline(TabularInline):
    model = Lesson
    extra = 1
    fields = ['title', 'slug', 'difficulty', 'order', 'reading_time', 'is_published']
    prepopulated_fields = {'slug': ('title',)}
    show_change_link = True


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    compressed_fields = True

    list_display = [
        'title', 'icon_preview', 'order', 'featured',
        'is_published', 'created_at', 'updated_at',
    ]
    list_filter = ['is_published', 'featured', 'created_at']
    list_editable = ['featured', 'is_published']
    search_fields = ['title', 'description', 'meta_title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order', 'title']
    inlines = [ChapterInline]
    list_per_page = 20
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'order', 'is_published', 'featured'),
        }),
        ('Icon Styling', {
            'fields': ('icon_html',),
            'description': (
                'Paste full HTML for the icon. Examples:<br>'
                '<code>&lt;i class="fa-brands fa-python"&gt;&lt;/i&gt;</code><br>'
                '<code>&lt;i class="fa-solid fa-database"&gt;&lt;/i&gt;</code>'
            ),
        }),
        ('SEO Configuration', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
            'description': 'Leave blank to auto-generate from title/description.',
        }),
        ('Media Assets', {
            'fields': ('image', 'image_alt'),
            'classes': ('collapse',),
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Icon View')
    def icon_preview(self, obj):
        if obj.icon_html:
            return format_html('<span style="font-size:1.25rem; color:#22C55E;">{}</span>', format_html(obj.icon_html))
        return "-"


@admin.register(Chapter)
class ChapterAdmin(ModelAdmin):
    compressed_fields = True

    list_display = ['title', 'topic', 'order', 'lesson_count', 'is_published', 'created_at']
    list_filter = ['is_published', 'topic']
    list_editable = ['is_published']
    search_fields = ['title', 'description', 'topic__title', 'meta_title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['topic__order', 'topic__title', 'order']
    inlines = [LessonInline]
    list_per_page = 20
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('topic', 'title', 'slug', 'description', 'estimated_hours', 'order', 'is_published'),
        }),
        ('Learning Material', {
            'fields': ('learning_objectives',),
        }),
        ('SEO Configuration', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
            'description': 'Leave blank to auto-generate from title/description.',
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Lessons Available')
    def lesson_count(self, obj):
        return obj.lessons.filter(is_published=True).count()


@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    compressed_fields = True

    list_display = [
        'title', 'chapter', 'status_badge', 'difficulty', 'order',
        'reading_time', 'featured', 'is_published', 'submitted_by', 'created_at',
    ]
    list_filter = ['status', 'is_published', 'difficulty', 'featured', 'chapter__topic', 'chapter']
    list_editable = ['featured', 'is_published']
    search_fields = ['title', 'summary', 'chapter__title', 'chapter__topic__title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['chapter__topic__title', 'chapter__order', 'order']
    list_per_page = 20
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    actions = ['publish_lessons', 'reject_lessons']

    fieldsets = (
        ('Lesson Identity', {
            'fields': (
                'chapter', 'title', 'slug', 'summary',
                'order', 'reading_time', 'is_published',
            ),
        }),
        ('Publication Status', {
            'fields': ('status', 'submitted_by', 'rejection_note', 'published_at'),
        }),
        ('Classification Parameters', {
            'fields': ('difficulty', 'featured'),
        }),
        ('Content Workspace (CKEditor 5)', {
            'fields': ('video_url', 'content'),
            'description': (
                'Add an optional video URL or write the full lesson content using the CKEditor 5 rich editor below. '
                'Use the toolbar for headings, lists, tables, images, and formatted content.'
            ),
        }),
        ('SEO Optimization', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
            'description': 'Leave blank to auto-generate from title/summary.',
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'draft': '#6b7280',
            'pending_review': '#f59e0b',
            'published': '#22c55e',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        label = obj.get_status_display()
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.78rem;">{}</span>',
            color, label
        )

    @admin.action(description='Publish selected lessons')
    def publish_lessons(self, request, queryset):
        count = 0
        for lesson in queryset:
            lesson.publish()
            count += 1
        self.message_user(request, f'{count} lesson(s) published.', messages.SUCCESS)

    @admin.action(description='Reject selected lessons')
    def reject_lessons(self, request, queryset):
        count = 0
        for lesson in queryset:
            lesson.reject()
            count += 1
        self.message_user(request, f'{count} lesson(s) rejected.', messages.SUCCESS)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('review/', self.admin_site.admin_view(self.review_lessons_view), name='lesson-review'),
            path('review/<int:pk>/approve/', self.admin_site.admin_view(self.approve_lesson_view), name='lesson-approve'),
            path('review/<int:pk>/reject/', self.admin_site.admin_view(self.reject_lesson_view), name='lesson-reject'),
        ]
        return custom_urls + urls

    def review_lessons_view(self, request):
        pending = Lesson.objects.filter(status='pending_review').select_related(
            'chapter', 'chapter__topic', 'submitted_by'
        ).order_by('created_at')
        return render(request, 'admin/learning/lesson/review.html', {
            'pending_lessons': pending,
            'title': 'Review Pending Lessons',
            'opts': self.model._meta,
        })

    def approve_lesson_view(self, request, pk):
        if request.method != 'POST':
            from django.http import HttpResponseNotAllowed
            return HttpResponseNotAllowed(['POST'])
        lesson = Lesson.objects.get(pk=pk)
        lesson.publish()
        self.message_user(request, f'Lesson "{lesson.title}" has been published.', messages.SUCCESS)
        return redirect('../')

    def reject_lesson_view(self, request, pk):
        if request.method == 'POST':
            lesson = Lesson.objects.get(pk=pk)
            note = request.POST.get('rejection_note', '')
            lesson.reject(note=note)
            self.message_user(request, f'Lesson "{lesson.title}" has been rejected.', messages.SUCCESS)
            return redirect('../')
        lesson = Lesson.objects.get(pk=pk)
        return render(request, 'admin/learning/lesson/reject_form.html', {
            'lesson': lesson,
            'title': 'Reject Lesson',
            'opts': self.model._meta,
        })


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'lesson', 'progress_pct', 'is_complete', 'last_viewed']
    list_filter = ['is_complete']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['user', 'lesson', 'progress_pct', 'is_complete', 'last_viewed']
    ordering = ['-last_viewed']
    list_per_page = 30

    def has_add_permission(self, request):
        return False


@admin.register(LessonBookmark)
class LessonBookmarkAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'lesson', 'created_at']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['user', 'lesson', 'created_at']
    ordering = ['-created_at']
    list_per_page = 30

    def has_add_permission(self, request):
        return False


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'lesson', 'viewed_at']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['user', 'lesson', 'viewed_at']
    ordering = ['-viewed_at']
    list_per_page = 30

    def has_add_permission(self, request):
        return False
