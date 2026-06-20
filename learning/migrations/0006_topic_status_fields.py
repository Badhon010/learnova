from django.db import migrations, models
import django.db.models.deletion


def set_topic_status_from_published(apps, schema_editor):
    Topic = apps.get_model('learning', 'Topic')
    Topic.objects.filter(is_published=True).update(status='published')
    Topic.objects.filter(is_published=False).update(status='draft')


def set_lesson_status_from_published(apps, schema_editor):
    Lesson = apps.get_model('learning', 'Lesson')
    Lesson.objects.filter(is_published=True).update(status='published')
    Lesson.objects.filter(is_published=False).exclude(status='draft').update(status='draft')
    Lesson.objects.filter(status='pending_review').update(status='draft', is_published=False)
    Lesson.objects.filter(status='rejected').update(status='draft', is_published=False)


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0005_topicproposal_approved_constraint'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('pending_review', 'Pending Review'),
                    ('changes_requested', 'Changes Requested'),
                    ('published', 'Published'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='topic',
            name='review_notes',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='topic',
            name='submitted_for_review_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='reviewed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reviewed_topics',
                to='auth.user',
            ),
        ),
        migrations.AlterField(
            model_name='topic',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='chapter',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('published', 'Published')],
                default='draft',
                max_length=20,
            ),
        ),
        migrations.RunPython(set_topic_status_from_published, migrations.RunPython.noop),
        migrations.RunPython(set_lesson_status_from_published, migrations.RunPython.noop),
    ]
