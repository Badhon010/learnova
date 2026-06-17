from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['user', 'role', 'website', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'bio']
    ordering = ['-created_at']
    list_per_page = 30
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['role']

    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'bio', 'avatar', 'website'),
        }),
        ('Social Links', {
            'fields': ('github_url', 'twitter_url', 'linkedin_url'),
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
