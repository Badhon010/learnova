from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Count, Avg, Q


def dashboard_callback(request, context):
    from learning.models import Topic, Chapter, Lesson, LessonBookmark, UserLessonProgress, LessonRating, LessonComment, Certificate
    from core.models import NewsletterSubscriber
    from quizzes.models import QuizAttempt

    topic_count = Topic.objects.count()
    lesson_count = Lesson.objects.count()
    published_count = Lesson.objects.filter(status='published').count()
    pending_count = Lesson.objects.filter(status='pending_review').count()
    subscriber_count = NewsletterSubscriber.objects.filter(is_active=True).count()
    user_count = User.objects.count()
    quiz_attempt_count = QuizAttempt.objects.count()
    comment_count = LessonComment.objects.filter(is_deleted=False).count()
    rating_count = LessonRating.objects.count()
    certificate_count = Certificate.objects.count()

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
                "description": "Total topics",
                "link": reverse("admin:learning_topic_changelist"),
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
            {
                "title": "Comments",
                "metric": str(comment_count),
                "icon": "chat",
                "description": "Active lesson comments",
                "link": reverse("admin:learning_lessoncomment_changelist"),
            },
            {
                "title": "Ratings",
                "metric": str(rating_count),
                "icon": "star",
                "description": "Lesson ratings submitted",
                "link": reverse("admin:learning_lessonrating_changelist"),
            },
            {
                "title": "Certificates",
                "metric": str(certificate_count),
                "icon": "workspace_premium",
                "description": "Certificates earned",
                "link": reverse("admin:learning_certificate_changelist"),
            },
        ],
        "analytics": _build_analytics(Lesson, LessonBookmark, UserLessonProgress, LessonRating, User),
    })

    return context


def _build_analytics(Lesson, LessonBookmark, UserLessonProgress, LessonRating, User):
    most_viewed = (
        Lesson.objects
        .filter(is_published=True)
        .annotate(view_count=Count('recent_views'))
        .order_by('-view_count')
        .values('title', 'view_count')[:5]
    )

    most_bookmarked = (
        Lesson.objects
        .filter(is_published=True)
        .annotate(bm_count=Count('bookmarks'))
        .order_by('-bm_count')
        .values('title', 'bm_count')[:5]
    )

    most_completed = (
        Lesson.objects
        .filter(is_published=True)
        .annotate(complete_count=Count(
            'progress_records',
            filter=Q(progress_records__is_complete=True),
        ))
        .order_by('-complete_count')
        .values('title', 'complete_count')[:5]
    )

    highest_rated = (
        Lesson.objects
        .filter(is_published=True, ratings__isnull=False)
        .annotate(avg_r=Avg('ratings__rating'), r_count=Count('ratings'))
        .filter(r_count__gte=1)
        .order_by('-avg_r')
        .values('title', 'avg_r', 'r_count')[:5]
    )

    top_contributors = (
        User.objects
        .annotate(pub_count=Count(
            'owned_topics',
            filter=Q(owned_topics__status='published'),
        ))
        .filter(pub_count__gt=0)
        .order_by('-pub_count')
        .values('username', 'pub_count')[:5]
    )

    return {
        'most_viewed': list(most_viewed),
        'most_bookmarked': list(most_bookmarked),
        'most_completed': list(most_completed),
        'highest_rated': list(highest_rated),
        'top_contributors': list(top_contributors),
    }
