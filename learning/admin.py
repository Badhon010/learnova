from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from .models import Topic, Chapter, Lesson


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
    compressed_fields = True  # Keeps form layouts tidy under Unfold
    
    list_display = [
        'title', 'icon_preview', 'order', 'featured',
        'is_published', 'created_at', 'updated_at',
    ]
    list_filter = ['is_published', 'featured', 'created_at']
    
    # REMOVED 'order' from here so it is no longer an editable input field on the list page
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
    
    # REMOVED 'order' from here as well
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
        'title', 'chapter', 'difficulty', 'order',
        'reading_time', 'featured', 'is_published', 'created_at',
    ]
    list_filter = ['is_published', 'difficulty', 'featured', 'chapter__topic', 'chapter']
    
    # REMOVED 'order' from here as well
    list_editable = ['featured', 'is_published']
    
    search_fields = ['title', 'summary', 'chapter__title', 'chapter__topic__title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['chapter__topic__title', 'chapter__order', 'order']
    list_per_page = 20
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Lesson Identity', {
            'fields': (
                'chapter', 'title', 'slug', 'summary',
                'order', 'reading_time', 'is_published',
            ),
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