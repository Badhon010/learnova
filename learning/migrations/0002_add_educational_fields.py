import decimal
from django.db import migrations, models
import django_ckeditor_5.fields


class Migration(migrations.Migration):

    dependencies = [
        ("learning", "0001_initial"),
    ]

    operations = [
        # --- Topic ---
        migrations.AddField(
            model_name="topic",
            name="image_alt",
            field=models.CharField(blank=True, max_length=255, help_text="Alt text for the topic image."),
        ),
        # --- Chapter ---
        migrations.AddField(
            model_name="chapter",
            name="learning_objectives",
            field=django_ckeditor_5.fields.CKEditor5Field(blank=True, help_text="What will learners achieve in this chapter?"),
        ),
        migrations.AddField(
            model_name="chapter",
            name="estimated_hours",
            field=models.DecimalField(decimal_places=1, default=decimal.Decimal("0.0"), help_text="Estimated hours to complete the chapter.", max_digits=4),
        ),
        migrations.AddField(
            model_name="chapter",
            name="meta_title",
            field=models.CharField(blank=True, help_text="SEO page title (max 60 chars). Auto-generated when blank.", max_length=60),
        ),
        migrations.AddField(
            model_name="chapter",
            name="meta_description",
            field=models.CharField(blank=True, help_text="SEO meta description (max 160 chars). Uses chapter description when blank.", max_length=160),
        ),
        # --- Lesson ---
        migrations.AddField(
            model_name="lesson",
            name="video_url",
            field=models.URLField(blank=True, help_text="Optional video URL (e.g. YouTube/Vimeo) for the lesson."),
        ),
    ]
