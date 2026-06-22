from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.db.models import Count, Q, Prefetch, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
import json

from .models import (
    Topic, Chapter, Lesson, LessonBookmark, UserLessonProgress,
    RecentlyViewed, LessonComment, CommentReply, LessonRating, Certificate,
    Notification, TopicProposal,
)


def _published_topics():
    return Topic.objects.filter(is_published=True).annotate(
        num_chapters=Count('chapters', filter=Q(chapters__is_published=True), distinct=True),
        num_lessons=Count(
            'chapters__lessons',
            filter=Q(chapters__is_published=True, chapters__lessons__is_published=True),
            distinct=True,
        ),
    )


def _published_lessons_prefetch():
    return Prefetch(
        'lessons',
        queryset=Lesson.objects.filter(is_published=True).order_by('order'),
    )


# ─── Topic / Chapter / Lesson ─────────────────────────────────────────────────

class TopicsView(ListView):
    model = Topic
    template_name = 'learning/topics.html'
    context_object_name = 'topics'
    paginate_by = 12

    def get_queryset(self):
        qs = _published_topics()
        search = self.request.GET.get('search', '').strip()
        difficulty = self.request.GET.get('difficulty', '').strip()
        if search:
            qs = qs.filter(title__icontains=search)
        if difficulty in ('beginner', 'intermediate', 'advanced'):
            qs = qs.filter(
                chapters__is_published=True,
                chapters__lessons__is_published=True,
                chapters__lessons__difficulty=difficulty,
            ).distinct()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search'] = self.request.GET.get('search', '')
        ctx['difficulty'] = self.request.GET.get('difficulty', '')
        ctx['total_count'] = Topic.objects.filter(is_published=True).count()
        return ctx


class TopicDetailView(DetailView):
    model = Topic
    template_name = 'learning/topic_detail.html'
    context_object_name = 'topic'

    def get_queryset(self):
        return _published_topics()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        topic = self.object
        chapters = (
            topic.chapters
            .filter(is_published=True)
            .prefetch_related(_published_lessons_prefetch())
            .annotate(num_lessons=Count('lessons', filter=Q(lessons__is_published=True), distinct=True))
            .order_by('order')
        )
        ctx['chapters'] = chapters
        ctx['breadcrumbs'] = [
            {'label': 'Topics', 'url': reverse('topics')},
            {'label': topic.title, 'url': None},
        ]
        return ctx


class ChapterDetailView(DetailView):
    model = Chapter
    template_name = 'learning/chapter_detail.html'
    context_object_name = 'chapter'
    slug_url_kwarg = 'chapter_slug'

    def get_queryset(self):
        return (
            Chapter.objects
            .filter(is_published=True)
            .select_related('topic')
            .annotate(num_lessons=Count('lessons', filter=Q(lessons__is_published=True), distinct=True))
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        chapter = self.object
        topic = chapter.topic
        ctx['topic'] = topic
        ctx['lessons'] = chapter.lessons.filter(is_published=True).order_by('order')
        ctx['chapters'] = (
            topic.chapters
            .filter(is_published=True)
            .annotate(num_lessons=Count('lessons', filter=Q(lessons__is_published=True), distinct=True))
            .order_by('order')
        )
        ctx['breadcrumbs'] = [
            {'label': 'Topics', 'url': reverse('topics')},
            {'label': topic.title, 'url': topic.get_absolute_url()},
            {'label': chapter.title, 'url': None},
        ]
        return ctx


class LessonDetailView(DetailView):
    model = Lesson
    template_name = 'learning/lesson_detail.html'
    context_object_name = 'lesson'

    def get_queryset(self):
        return (
            Lesson.objects
            .filter(is_published=True)
            .select_related('chapter', 'chapter__topic')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lesson = self.object
        chapter = lesson.chapter
        topic = chapter.topic

        all_chapters = (
            topic.chapters
            .filter(is_published=True)
            .prefetch_related(_published_lessons_prefetch())
            .order_by('order')
        )

        all_topic_lessons = list(
            Lesson.objects.filter(
                chapter__topic=topic,
                chapter__is_published=True,
                is_published=True,
            ).order_by('chapter__order', 'order').select_related('chapter')
        )

        current_idx = next(
            (i for i, l in enumerate(all_topic_lessons) if l.id == lesson.id), None
        )

        related_lessons = (
            Lesson.objects
            .filter(chapter=chapter, is_published=True)
            .exclude(pk=lesson.pk)
            .order_by('order')[:4]
        )

        ctx.update({
            'chapter': chapter,
            'topic': topic,
            'all_chapters': all_chapters,
            'chapter_lessons': list(chapter.lessons.filter(is_published=True).order_by('order')),
            'related_lessons': related_lessons,
            'prev_lesson': (
                all_topic_lessons[current_idx - 1]
                if current_idx and current_idx > 0 else None
            ),
            'next_lesson': (
                all_topic_lessons[current_idx + 1]
                if current_idx is not None and current_idx < len(all_topic_lessons) - 1
                else None
            ),
            'lesson_position': (current_idx + 1) if current_idx is not None else 1,
            'lesson_total': len(all_topic_lessons),
            'breadcrumbs': [
                {'label': 'Topics', 'url': reverse('topics')},
                {'label': topic.title, 'url': topic.get_absolute_url()},
                {'label': chapter.title, 'url': chapter.get_absolute_url()},
                {'label': lesson.title, 'url': None},
            ],
        })

        try:
            ctx['quiz'] = lesson.quiz
        except Exception:
            ctx['quiz'] = None

        ctx['comments'] = (
            LessonComment.objects
            .filter(lesson=lesson, is_deleted=False)
            .select_related('user')
            .prefetch_related(
                Prefetch(
                    'replies',
                    queryset=CommentReply.objects.filter(is_deleted=False).select_related('user'),
                )
            )
            .order_by('created_at')
        )
        ctx['comment_count'] = lesson.comment_count

        rating_agg = lesson.ratings.aggregate(avg=Avg('rating'))
        ctx['avg_rating'] = round(rating_agg['avg'], 1) if rating_agg['avg'] else None
        ctx['rating_count'] = lesson.ratings.count()

        if self.request.user.is_authenticated:
            ctx['is_bookmarked'] = LessonBookmark.objects.filter(
                user=self.request.user, lesson=lesson
            ).exists()
            ctx['user_progress'] = UserLessonProgress.objects.filter(
                user=self.request.user, lesson=lesson
            ).first()
            user_rating = LessonRating.objects.filter(
                user=self.request.user, lesson=lesson
            ).first()
            ctx['user_rating'] = user_rating.rating if user_rating else 0

            RecentlyViewed.objects.update_or_create(
                user=self.request.user, lesson=lesson, defaults={}
            )

            if ctx['quiz']:
                from quizzes.models import QuizAttempt
                ctx['best_attempt'] = (
                    QuizAttempt.objects
                    .filter(user=self.request.user, quiz=ctx['quiz'])
                    .order_by('-score').first()
                )
            else:
                ctx['best_attempt'] = None
        else:
            ctx.update({
                'is_bookmarked': False,
                'user_progress': None,
                'best_attempt': None,
                'user_rating': 0,
            })

        return ctx


# ─── Bookmark ─────────────────────────────────────────────────────────────────

@login_required
@require_POST
@csrf_protect
def bookmark_toggle_view(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug, is_published=True)
    bookmark, created = LessonBookmark.objects.get_or_create(user=request.user, lesson=lesson)
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True
    return JsonResponse({'bookmarked': bookmarked})


# ─── Reading Progress ─────────────────────────────────────────────────────────

@login_required
@require_POST
@csrf_protect
def update_progress_view(request):
    try:
        data = json.loads(request.body)
    except (ValueError, AttributeError):
        data = request.POST

    slug = data.get('lesson_slug', '')
    try:
        progress_pct = int(data.get('progress', 0))
        progress_pct = max(0, min(100, progress_pct))
    except (ValueError, TypeError):
        progress_pct = 0

    if not slug:
        return JsonResponse({'ok': False, 'error': 'No lesson_slug provided'}, status=400)

    lesson = get_object_or_404(Lesson, slug=slug, is_published=True)

    existing = UserLessonProgress.objects.filter(user=request.user, lesson=lesson).first()
    if existing and existing.progress_pct >= progress_pct:
        return JsonResponse({'ok': True, 'progress': existing.progress_pct})

    quiz_required = bool(lesson.required_quiz_questions and lesson.required_quiz_questions > 0)
    quiz_passed = False
    if quiz_required:
        try:
            from quizzes.models import QuizAttempt
            quiz_passed = QuizAttempt.objects.filter(
                user=request.user, quiz=lesson.quiz, passed=True
            ).exists()
        except Exception:
            quiz_passed = False

    can_complete = progress_pct >= 100 and (not quiz_required or quiz_passed)

    progress_obj, _ = UserLessonProgress.objects.update_or_create(
        user=request.user, lesson=lesson,
        defaults={
            'progress_pct': progress_pct,
            'is_complete': can_complete,
        },
    )

    RecentlyViewed.objects.update_or_create(user=request.user, lesson=lesson, defaults={})

    if can_complete:
        _check_and_issue_certificate(request.user, lesson)

    response_data = {'ok': True, 'progress': progress_pct}
    if quiz_required and progress_pct >= 100 and not quiz_passed:
        response_data['quiz_required'] = True
        response_data['message'] = 'Pass the lesson quiz to complete this lesson.'
    return JsonResponse(response_data)


def _check_and_issue_certificate(user, lesson):
    from .notifications import notify_certificate_earned
    topic = lesson.chapter.topic

    all_lesson_ids = set(
        Lesson.objects.filter(
            chapter__topic=topic,
            chapter__is_published=True,
            is_published=True,
        ).values_list('id', flat=True)
    )
    if not all_lesson_ids:
        return

    completed_ids = set(
        UserLessonProgress.objects.filter(
            user=user,
            lesson__id__in=all_lesson_ids,
            is_complete=True,
        ).values_list('lesson__id', flat=True)
    )

    if all_lesson_ids == completed_ids:
        cert, created = Certificate.objects.get_or_create(user=user, topic=topic)
        if created:
            notify_certificate_earned(cert)


# ─── Comments ─────────────────────────────────────────────────────────────────

@login_required
@require_POST
@csrf_protect
def add_comment_view(request, slug):
    from .notifications import notify_new_comment
    lesson = get_object_or_404(Lesson, slug=slug, is_published=True)
    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({'ok': False, 'error': 'Comment cannot be empty.'}, status=400)
    if len(content) > 5000:
        return JsonResponse({'ok': False, 'error': 'Comment is too long (max 5000 chars).'}, status=400)

    comment = LessonComment.objects.create(lesson=lesson, user=request.user, content=content)
    notify_new_comment(comment)

    try:
        avatar_url = request.user.profile.avatar.url if request.user.profile.avatar else ''
    except Exception:
        avatar_url = ''

    return JsonResponse({
        'ok': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'username': request.user.get_full_name() or request.user.username,
            'avatar': avatar_url,
            'created_at': comment.created_at.strftime('%b %d, %Y'),
        },
    })


@login_required
@require_POST
@csrf_protect
def delete_comment_view(request, pk):
    comment = get_object_or_404(LessonComment, pk=pk)
    can_delete = (
        comment.user == request.user
        or request.user.is_staff
        or (
            comment.lesson.chapter.topic.owner == request.user
            and hasattr(request.user, 'profile')
            and request.user.profile.is_contributor
        )
    )
    if not can_delete:
        return JsonResponse({'ok': False, 'error': 'Not allowed.'}, status=403)
    comment.is_deleted = True
    comment.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
@csrf_protect
def add_reply_view(request, comment_pk):
    comment = get_object_or_404(LessonComment, pk=comment_pk, is_deleted=False)
    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({'ok': False, 'error': 'Reply cannot be empty.'}, status=400)
    if len(content) > 2000:
        return JsonResponse({'ok': False, 'error': 'Reply is too long (max 2000 chars).'}, status=400)

    reply = CommentReply.objects.create(comment=comment, user=request.user, content=content)

    try:
        avatar_url = request.user.profile.avatar.url if request.user.profile.avatar else ''
    except Exception:
        avatar_url = ''

    return JsonResponse({
        'ok': True,
        'reply': {
            'id': reply.id,
            'content': reply.content,
            'username': request.user.get_full_name() or request.user.username,
            'avatar': avatar_url,
            'created_at': reply.created_at.strftime('%b %d, %Y'),
        },
    })


@login_required
@require_POST
@csrf_protect
def delete_reply_view(request, pk):
    reply = get_object_or_404(CommentReply, pk=pk)
    can_delete = (
        reply.user == request.user
        or request.user.is_staff
        or (
            reply.comment.lesson.chapter.topic.owner == request.user
            and hasattr(request.user, 'profile')
            and request.user.profile.is_contributor
        )
    )
    if not can_delete:
        return JsonResponse({'ok': False, 'error': 'Not allowed.'}, status=403)
    reply.is_deleted = True
    reply.save()
    return JsonResponse({'ok': True})


# ─── Ratings ──────────────────────────────────────────────────────────────────

@login_required
@require_POST
@csrf_protect
def rate_lesson_view(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug, is_published=True)
    try:
        rating_val = int(request.POST.get('rating', 0))
    except (ValueError, TypeError):
        rating_val = 0

    if rating_val not in range(1, 6):
        return JsonResponse({'ok': False, 'error': 'Rating must be 1–5.'}, status=400)

    LessonRating.objects.update_or_create(
        lesson=lesson, user=request.user,
        defaults={'rating': rating_val},
    )

    avg = lesson.ratings.aggregate(avg=Avg('rating'))['avg']
    avg_display = round(avg, 1) if avg else 0
    count = lesson.ratings.count()
    return JsonResponse({'ok': True, 'avg_rating': avg_display, 'rating_count': count, 'user_rating': rating_val})


# ─── Certificates ─────────────────────────────────────────────────────────────

def certificate_view(request, certificate_id):
    cert = get_object_or_404(Certificate, certificate_id=certificate_id)
    return render(request, 'learning/certificate.html', {'cert': cert})


def certificate_verify_view(request, certificate_id):
    cert = get_object_or_404(Certificate, certificate_id=certificate_id)
    return render(request, 'learning/certificate_verify.html', {'cert': cert})


# ─── Notifications ─────────────────────────────────────────────────────────────

@login_required
def notifications_view(request):
    notifications = (
        Notification.objects
        .filter(user=request.user)
        .order_by('-created_at')[:50]
    )
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'learning/notifications.html', {
        'notifications': notifications,
    })


@login_required
@require_POST
@csrf_protect
def mark_notification_read_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
@csrf_protect
def mark_all_notifications_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})


@login_required
def notifications_unread_count_view(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notifications_recent_api_view(request):
    from django.utils.timesince import timesince
    notifs = (
        Notification.objects
        .filter(user=request.user)
        .order_by('-created_at')[:8]
    )
    data = []
    for n in notifs:
        data.append({
            'id': n.id,
            'notif_type': n.notif_type,
            'icon': n.icon,
            'title': n.title,
            'url': n.url,
            'is_read': n.is_read,
            'created_at': timesince(n.created_at) + ' ago',
        })
    return JsonResponse({'notifications': data})


# ─── Topic Proposals ──────────────────────────────────────────────────────────

@login_required
def submit_topic_proposal_view(request):
    profile = request.user.profile
    if not profile.is_contributor:
        messages.error(request, 'Only contributors can submit topic proposals.')
        return redirect('dashboard')

    from .forms import TopicProposalForm
    if request.method == 'POST':
        form = TopicProposalForm(request.POST)
        action = request.POST.get('action', 'submit')
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.submitted_by = request.user
            proposal.status = 'pending_review' if action == 'submit' else 'draft'
            proposal.save()
            if action == 'submit':
                messages.success(request, f'Topic proposal "{proposal.title}" submitted for review!')
            else:
                messages.success(request, f'Topic proposal "{proposal.title}" saved as draft.')
            return redirect('my_proposals')
    else:
        form = TopicProposalForm()

    return render(request, 'learning/submit_topic_proposal.html', {'form': form})


@login_required
def my_proposals_view(request):
    profile = request.user.profile
    if not profile.is_contributor:
        messages.error(request, 'Only contributors can access topic proposals.')
        return redirect('dashboard')

    proposals = TopicProposal.objects.filter(submitted_by=request.user).order_by('-created_at')
    return render(request, 'learning/my_proposals.html', {
        'proposals': proposals,
        'profile': profile,
    })


@login_required
def edit_proposal_view(request, pk):
    proposal = get_object_or_404(TopicProposal, pk=pk, submitted_by=request.user)
    if proposal.status not in ('draft', 'rejected'):
        messages.error(request, 'Only draft or rejected proposals can be edited.')
        return redirect('my_proposals')

    from .forms import TopicProposalForm
    if request.method == 'POST':
        form = TopicProposalForm(request.POST, instance=proposal)
        action = request.POST.get('action', 'save')
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.status = 'pending_review' if action == 'submit' else 'draft'
            proposal.rejection_note = ''
            proposal.save()
            if action == 'submit':
                messages.success(request, f'Proposal "{proposal.title}" submitted for review!')
            else:
                messages.success(request, 'Proposal saved as draft.')
            return redirect('my_proposals')
    else:
        form = TopicProposalForm(instance=proposal)

    return render(request, 'learning/submit_topic_proposal.html', {
        'form': form,
        'proposal': proposal,
        'editing': True,
    })


@login_required
def delete_proposal_view(request, pk):
    proposal = get_object_or_404(TopicProposal, pk=pk, submitted_by=request.user)
    if proposal.status != 'draft':
        messages.error(request, 'Only draft proposals can be deleted.')
        return redirect('my_proposals')

    if request.method == 'POST':
        title = proposal.title
        proposal.delete()
        messages.success(request, f'Draft proposal "{title}" deleted.')
        return redirect('my_proposals')

    return render(request, 'learning/delete_proposal_confirm.html', {'proposal': proposal})


# ─── Staff Review Queue ────────────────────────────────────────────────────────

def _require_staff(request):
    if not request.user.is_authenticated:
        return redirect(f'/accounts/login/?next={request.path}')
    if not request.user.is_staff:
        messages.error(request, 'This area is restricted to staff members.')
        return redirect('dashboard')
    return None


@login_required
def staff_review_queue_view(request):
    """Staff-facing review dashboard — pending topic proposals and topics awaiting review."""
    err = _require_staff(request)
    if err:
        return err

    pending_proposals = (
        TopicProposal.objects
        .filter(status='pending_review')
        .select_related('submitted_by')
        .order_by('created_at')
    )
    pending_topics = (
        Topic.objects
        .filter(status='pending_review')
        .select_related('owner')
        .annotate(
            chapter_count=Count('chapters', distinct=True),
            lesson_count=Count('chapters__lessons', distinct=True),
        )
        .order_by('submitted_for_review_at')
    )
    recently_published = (
        Topic.objects
        .filter(status='published', is_published=True)
        .select_related('owner')
        .order_by('-reviewed_at')[:5]
    )
    return render(request, 'staff/review_queue.html', {
        'pending_proposals': pending_proposals,
        'pending_topics': pending_topics,
        'recently_published': recently_published,
        'pending_proposal_count': pending_proposals.count(),
        'pending_topic_count': pending_topics.count(),
    })


@login_required
def staff_review_topic_view(request, pk):
    """Staff review page for a single topic — approve, request changes, or reject."""
    err = _require_staff(request)
    if err:
        return err

    topic = get_object_or_404(Topic, pk=pk, status='pending_review')

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('review_notes', '').strip()

        if action == 'approve':
            topic.publish_topic(reviewed_by=request.user)
            from .notifications import notify_topic_published
            notify_topic_published(topic)
            messages.success(request, f'"{topic.title}" approved and published.')
            return redirect('staff_review_queue')

        elif action == 'request_changes':
            if not notes:
                messages.error(request, 'Please provide notes explaining what changes are needed.')
            else:
                topic.request_changes(notes=notes, reviewed_by=request.user)
                from .notifications import notify_topic_changes_requested
                notify_topic_changes_requested(topic)
                messages.success(request, f'Changes requested for "{topic.title}".')
                return redirect('staff_review_queue')

        elif action == 'reject':
            topic.reject_to_draft(notes=notes, reviewed_by=request.user)
            from .notifications import notify_topic_rejected_to_draft
            notify_topic_rejected_to_draft(topic)
            messages.success(request, f'"{topic.title}" rejected and moved to draft.')
            return redirect('staff_review_queue')

    chapters = (
        topic.chapters
        .prefetch_related(
            Prefetch('lessons', queryset=Lesson.objects.order_by('order'))
        )
        .annotate(lesson_count=Count('lessons', distinct=True))
        .order_by('order')
    )
    return render(request, 'staff/review_topic.html', {
        'topic': topic,
        'chapters': chapters,
    })


@login_required
def staff_approve_proposal_view(request, pk):
    err = _require_staff(request)
    if err:
        return err
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    proposal = get_object_or_404(TopicProposal, pk=pk, status='pending_review')
    proposal.approve()
    messages.success(request, f'Proposal "{proposal.title}" approved — topic created and assigned to {proposal.submitted_by.username}.')
    return redirect('staff_review_queue')


@login_required
def staff_reject_proposal_view(request, pk):
    err = _require_staff(request)
    if err:
        return err
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    proposal = get_object_or_404(TopicProposal, pk=pk, status='pending_review')
    note = request.POST.get('rejection_note', '').strip()
    proposal.reject(note=note)
    messages.success(request, f'Proposal "{proposal.title}" rejected.')
    return redirect('staff_review_queue')
