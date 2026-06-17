from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.core.mail import send_mail, send_mass_mail
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path
from unfold.admin import ModelAdmin
from .models import NewsletterCampaign
from core.models import NewsletterSubscriber


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ['subject', 'status', 'recipient_count', 'created_by', 'created_at', 'sent_at', 'campaign_actions']
    list_filter = ['status', 'created_at']
    search_fields = ['subject', 'body']
    readonly_fields = ['created_at', 'sent_at', 'recipient_count', 'status']
    ordering = ['-created_at']
    list_per_page = 20
    actions = ['send_campaign', 'send_test_email_action']

    fieldsets = (
        ('Campaign Details', {
            'fields': ('subject', 'preview_text', 'body', 'html_body'),
        }),
        ('Status', {
            'fields': ('status', 'recipient_count', 'created_by', 'created_at', 'sent_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Actions')
    def campaign_actions(self, obj):
        buttons = []
        if obj.status == 'draft':
            buttons.append(format_html(
                '<a href="/admin/newsletter/newslettercampaign/{}/send/" '
                'style="background:#22C55E;color:#fff;padding:3px 8px;border-radius:4px;font-size:0.78rem;text-decoration:none;margin-right:4px;">Send</a>',
                obj.pk
            ))
        buttons.append(format_html(
            '<a href="/admin/newsletter/newslettercampaign/{}/preview/" target="_blank" '
            'style="background:#3b82f6;color:#fff;padding:3px 8px;border-radius:4px;font-size:0.78rem;text-decoration:none;margin-right:4px;">Preview</a>',
            obj.pk
        ))
        if obj.status == 'draft':
            buttons.append(format_html(
                '<a href="/admin/newsletter/newslettercampaign/{}/test/" '
                'style="background:#8b5cf6;color:#fff;padding:3px 8px;border-radius:4px;font-size:0.78rem;text-decoration:none;">Test</a>',
                obj.pk
            ))
        if obj.status == 'sent':
            buttons.append(format_html('<span style="color:#16a34a;font-size:0.85rem;">✓ {}</span>', obj.recipient_count))
        return format_html(''.join(str(b) for b in buttons))

    @admin.action(description='Send selected campaigns to all active subscribers')
    def send_campaign(self, request, queryset):
        draft_campaigns = queryset.filter(status='draft')
        if not draft_campaigns.exists():
            self.message_user(request, 'No draft campaigns selected.', messages.WARNING)
            return

        subscribers = list(NewsletterSubscriber.objects.filter(is_active=True).values_list('email', flat=True))
        if not subscribers:
            self.message_user(request, 'No active subscribers found.', messages.WARNING)
            return

        sent_count = 0
        for campaign in draft_campaigns:
            datatuple = [
                (campaign.subject, campaign.body, None, [email])
                for email in subscribers
            ]
            try:
                send_mass_mail(datatuple, fail_silently=False)
                campaign.status = 'sent'
                campaign.sent_at = timezone.now()
                campaign.recipient_count = len(subscribers)
                campaign.save()
                sent_count += 1
            except Exception as e:
                self.message_user(request, f'Error sending "{campaign.subject}": {e}', messages.ERROR)

        if sent_count:
            self.message_user(
                request,
                f'Successfully sent {sent_count} campaign(s) to {len(subscribers)} subscribers.',
                messages.SUCCESS,
            )

    @admin.action(description='Send test email (to yourself) for selected campaigns')
    def send_test_email_action(self, request, queryset):
        if not request.user.email:
            self.message_user(request, 'Your admin account has no email address set.', messages.ERROR)
            return
        for campaign in queryset:
            try:
                send_mail(
                    subject=f'[TEST] {campaign.subject}',
                    message=campaign.body,
                    html_message=campaign.html_body or None,
                    from_email=None,
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                self.message_user(request, f'Error sending test for "{campaign.subject}": {e}', messages.ERROR)
                continue
        self.message_user(request, f'Test email(s) sent to {request.user.email}.', messages.SUCCESS)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:campaign_id>/send/', self.admin_site.admin_view(self.send_single_view), name='newsletter-send'),
            path('<int:campaign_id>/preview/', self.admin_site.admin_view(self.preview_view), name='newsletter-preview'),
            path('<int:campaign_id>/test/', self.admin_site.admin_view(self.send_test_view), name='newsletter-test'),
        ]
        return custom_urls + urls

    def send_single_view(self, request, campaign_id):
        campaign = get_object_or_404(NewsletterCampaign, id=campaign_id)
        if campaign.status != 'draft':
            self.message_user(request, 'This campaign has already been sent.', messages.WARNING)
            return redirect('admin:newsletter_newslettercampaign_changelist')

        if request.method == 'GET':
            subscriber_count = NewsletterSubscriber.objects.filter(is_active=True).count()
            return render(request, 'admin/newsletter/send_confirm.html', {
                'campaign': campaign,
                'subscriber_count': subscriber_count,
                'title': 'Confirm: Send Campaign',
                'opts': NewsletterCampaign._meta,
            })

        subscribers = list(NewsletterSubscriber.objects.filter(is_active=True).values_list('email', flat=True))
        if not subscribers:
            self.message_user(request, 'No active subscribers found.', messages.WARNING)
            return redirect('admin:newsletter_newslettercampaign_changelist')

        datatuple = [
            (campaign.subject, campaign.body, None, [email])
            for email in subscribers
        ]
        try:
            send_mass_mail(datatuple, fail_silently=False)
            campaign.status = 'sent'
            campaign.sent_at = timezone.now()
            campaign.recipient_count = len(subscribers)
            campaign.save()
            self.message_user(
                request,
                f'Campaign "{campaign.subject}" sent to {len(subscribers)} subscribers.',
                messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(request, f'Error sending campaign: {e}', messages.ERROR)

        return redirect('admin:newsletter_newslettercampaign_changelist')

    def preview_view(self, request, campaign_id):
        campaign = get_object_or_404(NewsletterCampaign, id=campaign_id)
        html = campaign.html_body or f'<pre style="font-family:sans-serif;white-space:pre-wrap;">{campaign.body}</pre>'
        full_html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Preview: {campaign.subject}</title>
<style>body{{font-family:sans-serif;max-width:680px;margin:40px auto;padding:20px;}}
.preview-bar{{background:#1e293b;color:#fff;padding:12px 20px;border-radius:8px;margin-bottom:24px;font-size:0.9rem;}}
</style>
</head><body>
<div class="preview-bar">
  <strong>Subject:</strong> {campaign.subject}
  {f'<br><strong>Preview text:</strong> {campaign.preview_text}' if campaign.preview_text else ''}
  <br><strong>Status:</strong> {campaign.get_status_display()}
  &nbsp;|&nbsp; <strong>Subscribers:</strong> {NewsletterSubscriber.objects.filter(is_active=True).count()} active
</div>
{html}
</body></html>'''
        from django.http import HttpResponse
        return HttpResponse(full_html)

    def send_test_view(self, request, campaign_id):
        campaign = get_object_or_404(NewsletterCampaign, id=campaign_id)

        if request.method == 'GET':
            return render(request, 'admin/newsletter/test_confirm.html', {
                'campaign': campaign,
                'admin_email': request.user.email or '(no email set)',
                'title': 'Confirm: Send Test Email',
                'opts': NewsletterCampaign._meta,
            })

        if not request.user.email:
            self.message_user(request, 'Your admin account has no email address set.', messages.ERROR)
            return redirect('admin:newsletter_newslettercampaign_changelist')
        try:
            send_mail(
                subject=f'[TEST] {campaign.subject}',
                message=campaign.body,
                html_message=campaign.html_body or None,
                from_email=None,
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            self.message_user(
                request,
                f'Test email sent to {request.user.email}.',
                messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(request, f'Error sending test: {e}', messages.ERROR)
        return redirect('admin:newsletter_newslettercampaign_changelist')
