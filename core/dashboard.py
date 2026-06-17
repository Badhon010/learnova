from django.contrib.auth.models import User
from django.urls import reverse


def dashboard_callback(request, context):
    from learning.models import Topic, Chapter, Lesson
    from core.models import NewsletterSubscriber
    from quizzes.models import QuizAttempt

    topic_count = Topic.objects.count()
    chapter_count = Chapter.objects.count()
    lesson_count = Lesson.objects.count()
    published_count = Lesson.objects.filter(status='published').count()
    pending_count = Lesson.objects.filter(status='pending_review').count()
    subscriber_count = NewsletterSubscriber.objects.filter(is_active=True).count()
    user_count = User.objects.count()
    quiz_attempt_count = QuizAttempt.objects.count()

    context.update({
        "kpi": [
            {
                "title": "Users",
                "metric": str(user_count),
                "icon": "person",
                "description": "Registered accounts",
                "link": reverse("admin:auth_user_changelist"),
            },
            {
                "title": "Topics",
                "metric": str(topic_count),
                "icon": "book",
                "description": "Published topics",
                "link": reverse("admin:learning_topic_changelist"),
            },
            {
                "title": "Chapters",
                "metric": str(chapter_count),
                "icon": "layers",
                "description": "Total chapters",
                "link": reverse("admin:learning_chapter_changelist"),
            },
            {
                "title": "Lessons",
                "metric": str(lesson_count),
                "icon": "article",
                "description": "Total lessons",
                "link": reverse("admin:learning_lesson_changelist"),
            },
            {
                "title": "Published",
                "metric": str(published_count),
                "icon": "check_circle",
                "description": "Published lessons",
                "link": reverse("admin:learning_lesson_changelist"),
            },
            {
                "title": "Pending Review",
                "metric": str(pending_count),
                "icon": "rate_review",
                "description": "Awaiting admin review",
                "link": f"{reverse('admin:learning_lesson_changelist')}?status__exact=pending_review",
            },
            {
                "title": "Subscribers",
                "metric": str(subscriber_count),
                "icon": "mail",
                "description": "Active newsletter subscribers",
                "link": reverse("admin:core_newslettersubscriber_changelist"),
            },
            {
                "title": "Quiz Attempts",
                "metric": str(quiz_attempt_count),
                "icon": "quiz",
                "description": "Total quiz attempts",
                "link": reverse("admin:quizzes_quizattempt_changelist"),
            },
        ]
    })

    return context
