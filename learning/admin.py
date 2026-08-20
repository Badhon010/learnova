from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    Topic, Chapter, Lesson, UserLessonProgress, LessonBookmark, RecentlyViewed,
    LessonComment, CommentReply, LessonRating, Certificate,
    Notification, TopicProposal,
)


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
        'title', 'status', 'order', 'featured',
        'is_published', 'owner', 'created_at',
    ]
    list_filter = ['status', 'is_published', 'featured', 'created_at']
    list_editable = ['featured']
    search_fields = ['title', 'description', 'meta_title', 'owner__username']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order', 'title']
    inlines = [ChapterInline]
    list_per_page = 20
    readonly_fields = [
        'created_at', 'updated_at', 'submitted_for_review_at',
        'reviewed_at', 'reviewed_by', 'icon_preview',
    ]

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'order', 'is_published', 'featured', 'owner'),
        }),
        ('Publication Workflow', {
            'fields': ('status', 'review_notes', 'submitted_for_review_at', 'reviewed_at', 'reviewed_by'),
            'description': (
                'Topic status is managed by the contributor workflow. '
                'Use the staff review queue at <code>/review/</code> to approve or reject topics.'
            ),
        }),
        ('Icon Styling', {
            'fields': ('icon_html', 'icon_preview'),
            'description': (
                'Paste a Font Awesome snippet or inline SVG. Markup is sanitized and '
                'the preview is constrained to the admin field size.<br>'
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
            return format_html(
                '<span class="topic-icon topic-icon-admin" '
                'style="display:inline-flex;align-items:center;justify-content:center;'
                'width:2.5rem;height:2.5rem;max-width:100%;overflow:hidden;'
                'font-size:1.5rem;color:#22C55E;line-height:1;">{}</span>',
                obj.safe_icon_html,
            )
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
        'reading_time', 'featured', 'is_published', 'created_at',
    ]
    list_filter = ['status', 'is_published', 'difficulty', 'featured', 'chapter__topic', 'chapter']
    list_editable = ['featured', 'is_published']
    search_fields = ['title', 'summary', 'chapter__title', 'chapter__topic__title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['chapter__topic__title', 'chapter__order', 'order']
    list_per_page = 20
    readonly_fields = ['created_at', 'updated_at', 'published_at']

    fieldsets = (
        ('Lesson Identity', {
            'fields': (
                'chapter', 'title', 'slug', 'summary',
                'order', 'reading_time', 'is_published',
            ),
        }),
        ('Quiz Requirement', {
            'fields': ('required_quiz_questions',),
            'description': (
                'Set a number to require passing a quiz before this lesson can be marked complete. '
                'Leave blank for normal completion.'
            ),
        }),
        ('Publication Status', {
            'fields': ('status', 'published_at'),
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
            'published': '#22c55e',
        }
        color = colors.get(obj.status, '#6b7280')
        label = obj.get_status_display()
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.78rem;">{}</span>',
            color, label
        )


@admin.register(TopicProposal)
class TopicProposalAdmin(ModelAdmin):
    compressed_fields = True

    list_display = [
        'title', 'submitted_by', 'status_badge', 'created_at', 'updated_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'submitted_by__username']
    readonly_fields = ['submitted_by', 'status', 'created_at', 'updated_at', 'approved_topic']
    ordering = ['-created_at']
    list_per_page = 20
    actions = ['approve_proposals', 'reject_proposals']

    fieldsets = (
        (None, {
            'fields': ('submitted_by', 'title', 'description', 'icon_html'),
        }),
        ('Review', {
            'fields': ('status', 'rejection_note', 'approved_topic'),
            'description': (
                '<strong>⚠ Status is read-only.</strong> '
                'Use the <em>Approve</em> or <em>Reject</em> actions to change proposal status. '
                'Manual status edits are blocked to prevent orphaned approvals.'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'draft': '#6b7280',
            'pending_review': '#f59e0b',
            'approved': '#22c55e',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.78rem;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.action(description='Approve selected topic proposals')
    def approve_proposals(self, request, queryset):
        count = 0
        for proposal in queryset.filter(status='pending_review'):
            proposal.approve()
            count += 1
        self.message_user(request, f'{count} proposal(s) approved and topics created.', messages.SUCCESS)

    @admin.action(description='Reject selected topic proposals')
    def reject_proposals(self, request, queryset):
        count = 0
        for proposal in queryset.filter(status='pending_review'):
            proposal.reject(note='Not approved at this time.')
            count += 1
        self.message_user(request, f'{count} proposal(s) rejected.', messages.SUCCESS)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/approve/', self.admin_site.admin_view(self.approve_view), name='topicproposal-approve'),
            path('<int:pk>/reject/', self.admin_site.admin_view(self.reject_view), name='topicproposal-reject'),
        ]
        return custom_urls + urls

    def approve_view(self, request, pk):
        if request.method != 'POST':
            from django.http import HttpResponseNotAllowed
            return HttpResponseNotAllowed(['POST'])
        proposal = TopicProposal.objects.get(pk=pk)
        proposal.approve()
        self.message_user(request, f'Proposal "{proposal.title}" approved and topic created.', messages.SUCCESS)
        return redirect('../../')

    def reject_view(self, request, pk):
        if request.method == 'POST':
            proposal = TopicProposal.objects.get(pk=pk)
            note = request.POST.get('rejection_note', '')
            proposal.reject(note=note)
            self.message_user(request, f'Proposal "{proposal.title}" rejected.', messages.SUCCESS)
            return redirect('../../')
        proposal = TopicProposal.objects.get(pk=pk)
        return render(request, 'admin/learning/topicproposal/reject_form.html', {
            'proposal': proposal,
            'title': 'Reject Proposal',
            'opts': self.model._meta,
        })


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'notif_type', 'title', 'is_read', 'created_at']
    list_filter = ['notif_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['user', 'notif_type', 'title', 'message', 'url', 'created_at']
    ordering = ['-created_at']
    list_per_page = 30
    actions = ['mark_read', 'mark_unread']

    @admin.action(description='Mark selected as read')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Mark selected as unread')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)

    def has_add_permission(self, request):
        return False


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


@admin.register(LessonComment)
class LessonCommentAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'lesson_link', 'content_preview', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['user__username', 'lesson__title', 'content']
    readonly_fields = ['user', 'lesson', 'created_at']
    ordering = ['-created_at']
    list_per_page = 30
    actions = ['mark_deleted', 'mark_restored']

    def lesson_link(self, obj):
        return format_html('<a href="{}">{}</a>', obj.lesson.get_absolute_url(), obj.lesson.title)
    lesson_link.short_description = 'Lesson'

    def content_preview(self, obj):
        return obj.content[:80] + ('…' if len(obj.content) > 80 else '')
    content_preview.short_description = 'Content'

    @admin.action(description='Mark selected comments as deleted')
    def mark_deleted(self, request, queryset):
        queryset.update(is_deleted=True)

    @admin.action(description='Restore selected comments')
    def mark_restored(self, request, queryset):
        queryset.update(is_deleted=False)

    def has_add_permission(self, request):
        return False


@admin.register(CommentReply)
class CommentReplyAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'comment', 'content_preview', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['user', 'comment', 'created_at']
    ordering = ['-created_at']
    list_per_page = 30

    def content_preview(self, obj):
        return obj.content[:80] + ('…' if len(obj.content) > 80 else '')
    content_preview.short_description = 'Content'

    def has_add_permission(self, request):
        return False


@admin.register(LessonRating)
class LessonRatingAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'lesson', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['user', 'lesson', 'rating', 'created_at']
    ordering = ['-created_at']
    list_per_page = 30

    def has_add_permission(self, request):
        return False


@admin.register(Certificate)
class CertificateAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'topic', 'issued_at', 'certificate_link']
    list_filter = ['issued_at', 'topic']
    search_fields = ['user__username', 'topic__title']
    readonly_fields = ['user', 'topic', 'certificate_id', 'issued_at']
    ordering = ['-issued_at']
    list_per_page = 30

    def certificate_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">View</a>',
            obj.get_absolute_url(),
        )
    certificate_link.short_description = 'Certificate'

    def has_add_permission(self, request):
        return False
