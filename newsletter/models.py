from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class NewsletterCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    ]

    subject = models.CharField(max_length=300)
    body = models.TextField(help_text='Plain text content of the email.')
    html_body = models.TextField(blank=True, help_text='Optional HTML version. If blank, plain text is used.')
    preview_text = models.CharField(
        max_length=255, blank=True,
        help_text='Short preview text shown in email clients after the subject line.',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    recipient_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter Campaign'
        verbose_name_plural = 'Newsletter Campaigns'

    def __str__(self):
        return f'{self.subject} ({self.status})'
