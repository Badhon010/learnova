from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0004_topic_owner_chapter_created_by'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='topicproposal',
            constraint=models.CheckConstraint(
                check=~models.Q(status='approved') | models.Q(approved_topic__isnull=False),
                name='topicproposal_approved_requires_topic',
            ),
        ),
    ]
