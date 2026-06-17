from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsletterCampaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=300)),
                ('body', models.TextField(help_text='Plain text content of the email.')),
                ('html_body', models.TextField(blank=True, help_text='Optional HTML version. If blank, plain text is used.')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent')], default='draft', max_length=10)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('recipient_count', models.PositiveIntegerField(default=0)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Newsletter Campaign',
                'verbose_name_plural': 'Newsletter Campaigns',
                'ordering': ['-created_at'],
            },
        ),
    ]
