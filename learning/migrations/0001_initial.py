from django.db import migrations, models
import django.db.models.deletion
import django_ckeditor_5.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Topic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("description", models.TextField()),
                ("icon_html", models.TextField(default='<i class="fa-solid fa-book"></i>', help_text='Full HTML icon. E.g. <code>&lt;i class="fa-brands fa-python"&gt;&lt;/i&gt;</code> or an inline SVG.')),
                ("image", models.ImageField(blank=True, null=True, upload_to="topics/")),
                ("meta_title", models.CharField(blank=True, help_text="SEO page title (max 60 chars). Auto-generated when blank.", max_length=60)),
                ("meta_description", models.CharField(blank=True, help_text="SEO meta description (max 160 chars). Uses topic description when blank.", max_length=160)),
                ("featured", models.BooleanField(default=False, help_text="Show in the Featured Topics section on the homepage.")),
                ("order", models.PositiveIntegerField(default=0, help_text="Display order on the topics listing page")),
                ("is_published", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["order", "title"]},
        ),
        migrations.CreateModel(
            name="Chapter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("description", models.TextField()),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_published", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("topic", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chapters", to="learning.topic")),
            ],
            options={"ordering": ["order", "title"]},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("summary", models.TextField()),
                ("content", django_ckeditor_5.fields.CKEditor5Field(blank=True, help_text="Full lesson content. Use CKEditor 5 to add headings, images, links, lists, tables, and more.")),
                ("difficulty", models.CharField(choices=[("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")], default="beginner", help_text="Difficulty level displayed to learners.", max_length=15)),
                ("meta_title", models.CharField(blank=True, help_text="SEO page title (max 60 chars). Auto-generated when blank.", max_length=60)),
                ("meta_description", models.CharField(blank=True, help_text="SEO meta description (max 160 chars). Uses lesson summary when blank.", max_length=160)),
                ("featured", models.BooleanField(default=False, help_text="Show in the Featured / Popular Lessons section on the homepage.")),
                ("order", models.PositiveIntegerField(default=0)),
                ("reading_time", models.PositiveIntegerField(default=5, help_text="Estimated reading time in minutes")),
                ("is_published", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("chapter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="learning.chapter")),
            ],
            options={"ordering": ["order", "title"]},
        ),
    ]
