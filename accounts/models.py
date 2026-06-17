from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('reader', 'Reader'),
        ('contributor', 'Contributor'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, help_text='Short bio about yourself.')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reader')
    website = models.URLField(blank=True)
    github_url = models.URLField(blank=True, null=True, help_text='Your GitHub profile URL.')
    twitter_url = models.URLField(blank=True, null=True, help_text='Your Twitter/X profile URL.')
    linkedin_url = models.URLField(blank=True, null=True, help_text='Your LinkedIn profile URL.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'{self.user.username} ({self.role})'

    @property
    def is_contributor(self):
        return self.role == 'contributor'

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
