from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin

# Import ModelAdmin directly from the main admin bundle
from unfold.admin import ModelAdmin
# Import the styled forms to make password/user modification screens look correct
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import NewsletterSubscriber, ContactMessage

# -----------------------------------------------------------------------------
# Authentication & Authorization Overrides (Unfold Theme)
# -----------------------------------------------------------------------------
admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    compressed_fields = True
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class CustomGroupAdmin(BaseGroupAdmin, ModelAdmin):
    compressed_fields = True

# -----------------------------------------------------------------------------
# Application Models
# -----------------------------------------------------------------------------

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(ModelAdmin):
    compressed_fields = True  # Optimizes layout grid spacing
    
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active']
    search_fields = ['email']
    ordering = ['-subscribed_at']
    list_per_page = 50
    actions = ['mark_active', 'mark_inactive']

    @admin.action(description='Mark selected as active')
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, 'Selected subscribers marked as active.')

    @admin.action(description='Mark selected as inactive')
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, 'Selected subscribers marked as inactive.')


@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    compressed_fields = True
    
    list_display = ['name', 'email', 'subject', 'is_read', 'sent_at']
    list_filter = ['is_read', 'sent_at']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering = ['-sent_at']
    list_per_page = 30
    readonly_fields = ['name', 'email', 'subject', 'message', 'sent_at']
    actions = ['mark_read', 'mark_unread']

    @admin.action(description='Mark selected as read')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, 'Messages marked as read.')

    @admin.action(description='Mark selected as unread')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, 'Messages marked as unread.')