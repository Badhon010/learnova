"""
Learnova — Notification helpers.
Creates in-app Notification records AND optionally sends email.
All operations are wrapped in try/except so failures never break requests.
"""
from django.core.mail import send_mail
from django.conf import settings


def _send_email(subject, message, recipient_email):
    if not recipient_email:
        return
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=True,
        )
    except Exception:
        pass


def _notif(user, notif_type, title, message, url=''):
    """Create an in-app notification (safe — never raises)."""
    try:
        from learning.models import Notification
        Notification.create(user=user, notif_type=notif_type, title=title, message=message, url=url)
    except Exception:
        pass


# ── Topic Review Notifications ─────────────────────────────────────────────────

def notify_topic_review_submitted(topic):
    """Notify all staff that a contributor submitted a topic for review."""
    from django.contrib.auth.models import User
    staff_users = User.objects.filter(is_staff=True)
    review_url = f'/review/topics/{topic.pk}/'
    for staff in staff_users:
        _notif(
            staff,
            'topic_review_submitted',
            title=f'Topic "{topic.title}" submitted for review',
            message=(
                f'{topic.owner.username if topic.owner else "A contributor"} submitted '
                f'"{topic.title}" for staff review.'
            ),
            url=review_url,
        )


def notify_topic_published(topic):
    """Notify contributor that their topic was approved and published."""
    if not topic.owner:
        return
    user = topic.owner
    url = topic.get_absolute_url()
    title = f'"{topic.title}" is now published!'
    message = (
        f'Great news! Your topic "{topic.title}" has been reviewed and approved. '
        f'It is now publicly visible on Learnova.'
    )
    _notif(user, 'topic_published', title, message, url=url)
    _send_email(
        subject=f'[Learnova] {title}',
        message=(
            f'Hi {user.get_full_name() or user.username},\n\n'
            f'{message}\n\n'
            f'View it here: {getattr(settings, "SITE_URL", "")}{url}\n\n'
            f'The Learnova Team'
        ),
        recipient_email=user.email,
    )


def notify_topic_changes_requested(topic):
    """Notify contributor that staff requested changes."""
    if not topic.owner:
        return
    user = topic.owner
    hub_url = '/accounts/my-lessons/'
    title = f'Changes requested for "{topic.title}"'
    notes_text = f'\n\nReviewer notes: {topic.review_notes}' if topic.review_notes else ''
    message = (
        f'A staff member reviewed "{topic.title}" and requested some changes '
        f'before it can be published.{notes_text}'
    )
    _notif(user, 'topic_changes_requested', title, message, url=hub_url)
    _send_email(
        subject=f'[Learnova] {title}',
        message=(
            f'Hi {user.get_full_name() or user.username},\n\n'
            f'{message}\n\n'
            f'Head to your Contributor Hub to make the changes: '
            f'{getattr(settings, "SITE_URL", "")}{hub_url}\n\n'
            f'The Learnova Team'
        ),
        recipient_email=user.email,
    )


def notify_topic_rejected_to_draft(topic):
    """Notify contributor that their topic was rejected back to draft."""
    if not topic.owner:
        return
    user = topic.owner
    hub_url = '/accounts/my-lessons/'
    title = f'"{topic.title}" was not approved'
    notes_text = f'\n\nReviewer notes: {topic.review_notes}' if topic.review_notes else ''
    message = (
        f'Your topic "{topic.title}" was reviewed but not approved at this time. '
        f'It has been moved back to draft.{notes_text}'
    )
    _notif(user, 'topic_rejected_to_draft', title, message, url=hub_url)
    _send_email(
        subject=f'[Learnova] {title}',
        message=(
            f'Hi {user.get_full_name() or user.username},\n\n'
            f'{message}\n\n'
            f'You can revise and resubmit from your Contributor Hub: '
            f'{getattr(settings, "SITE_URL", "")}{hub_url}\n\n'
            f'The Learnova Team'
        ),
        recipient_email=user.email,
    )


# ── Comment Notifications ──────────────────────────────────────────────────────

def notify_new_comment(comment):
    lesson = comment.lesson
    if not lesson.submitted_by or lesson.submitted_by == comment.user:
        return
    user = lesson.submitted_by
    commenter = comment.user.get_full_name() or comment.user.username
    title = f'New comment on "{lesson.title}"'
    message = f'{commenter} commented: "{comment.content[:200]}"'
    _notif(user, 'new_comment', title, message, url=lesson.get_absolute_url() + '#comments')
    _send_email(
        subject=f'[Learnova] {title}',
        message=(
            f'Hi {user.get_full_name() or user.username},\n\n'
            f'{commenter} commented on your lesson "{lesson.title}":\n\n'
            f'"{comment.content[:300]}"\n\n'
            f'View: {getattr(settings, "SITE_URL", "")}{lesson.get_absolute_url()}#comments\n\n'
            f'The Learnova Team'
        ),
        recipient_email=user.email,
    )


# ── Certificate Notifications ─────────────────────────────────────────────────

def notify_certificate_earned(certificate):
    user = certificate.user
    title = f'Certificate earned: {certificate.topic.title}'
    message = (
        f'Congratulations! You completed all lessons in "{certificate.topic.title}" '
        f'and earned your certificate.'
    )
    _notif(user, 'certificate_earned', title, message, url=certificate.get_absolute_url())
    _send_email(
        subject=f'[Learnova] {title}',
        message=(
            f'Congratulations {user.get_full_name() or user.username}!\n\n'
            f'{message}\n\n'
            f'View your certificate: {getattr(settings, "SITE_URL", "")}{certificate.get_absolute_url()}\n\n'
            f'The Learnova Team'
        ),
        recipient_email=user.email,
    )


# ── Quiz Notifications ─────────────────────────────────────────────────────────

def notify_quiz_passed(attempt):
    user = attempt.user
    title = f'You passed: {attempt.quiz.title}'
    message = f'You scored {attempt.score}% on "{attempt.quiz.title}". Well done!'
    lesson_url = ''
    if attempt.quiz.lesson:
        lesson_url = attempt.quiz.lesson.get_absolute_url()
    _notif(user, 'quiz_passed', title, message, url=lesson_url)
