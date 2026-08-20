from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.text import slugify
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
import uuid

from .forms import (
    RegisterForm, LoginForm, ProfileEditForm,
    LessonEditForm,
    ChapterCreateForm, LessonCreateForChapterForm, TopicEditForm,
)
from .models import UserProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Learnova, {user.username}!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard_view(request):
    from learning.models import (
        Topic, Lesson, UserLessonProgress, LessonBookmark,
        RecentlyViewed, Certificate, Notification,
    )
    from quizzes.models import QuizAttempt

    profile = request.user.profile

    progress_qs = UserLessonProgress.objects.filter(user=request.user)
    lessons_started = progress_qs.count()
    lessons_completed = progress_qs.filter(is_complete=True).count()

    recently_viewed = (
        RecentlyViewed.objects
        .filter(user=request.user)
        .select_related('lesson', 'lesson__chapter', 'lesson__chapter__topic')
        .order_by('-viewed_at')[:10]
    )
    rv_lesson_ids = [rv.lesson_id for rv in recently_viewed]
    progress_map = {
        p.lesson_id: p
        for p in UserLessonProgress.objects.filter(
            user=request.user, lesson_id__in=rv_lesson_ids
        )
    }
    continue_learning = []
    for rv in recently_viewed[:5]:
        prog = progress_map.get(rv.lesson_id)
        continue_learning.append({
            'lesson': rv.lesson,
            'progress': prog.progress_pct if prog else 0,
            'is_complete': prog.is_complete if prog else False,
        })

    bookmarks = (
        LessonBookmark.objects
        .filter(user=request.user)
        .select_related('lesson', 'lesson__chapter', 'lesson__chapter__topic')
        .order_by('-created_at')[:5]
    )

    from django.db.models import Avg as _Avg, Count as _Count
    quiz_stats = QuizAttempt.objects.filter(user=request.user).aggregate(
        total=_Count('id'),
        avg=_Avg('score'),
    )
    quizzes_completed = quiz_stats['total'] or 0
    avg_score = round(quiz_stats['avg']) if quiz_stats['avg'] else 0

    certificates = (
        Certificate.objects
        .filter(user=request.user)
        .select_related('topic')
        .order_by('-issued_at')
    )

    unread_notif_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'profile': profile,
        'topic_count': Topic.objects.filter(is_published=True).count(),
        'lesson_count': Lesson.objects.filter(is_published=True).count(),
        'lessons_started': lessons_started,
        'lessons_completed': lessons_completed,
        'continue_learning': continue_learning,
        'recently_viewed': recently_viewed,
        'bookmarks': bookmarks,
        'quizzes_completed': quizzes_completed,
        'avg_score': avg_score,
        'certificates': certificates,
        'unread_notif_count': unread_notif_count,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_edit_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


def profile_detail_view(request, username):
    user = get_object_or_404(User, username=username)
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        raise Http404

    from learning.models import Lesson
    published_lessons = (
        Lesson.objects
        .filter(chapter__topic__owner=user, is_published=True, status='published')
        .select_related('chapter', 'chapter__topic')
        .order_by('-published_at')
    )

    return render(request, 'accounts/profile_detail.html', {
        'profile_user': user,
        'profile': profile,
        'published_lessons': published_lessons,
    })


# ─── Contributor Hub ──────────────────────────────────────────────────────────

def _require_contributor(request):
    """Returns (profile, None) if ok, or (None, redirect_response) if not."""
    profile = request.user.profile
    if not profile.is_contributor:
        messages.error(request, 'Only contributors can access this area.')
        return None, redirect('dashboard')
    return profile, None


@login_required
def my_lessons_view(request):
    """Contributor hub — owned topics grouped by status."""
    profile, err = _require_contributor(request)
    if err:
        return err

    from learning.models import TopicProposal, Topic, Chapter
    from django.db.models import Count, Q as _Q

    owned_topics = (
        Topic.objects
        .filter(owner=request.user)
        .annotate(
            chapter_count=Count('chapters', distinct=True),
            lesson_count=Count('chapters__lessons', distinct=True),
        )
        .order_by('status', 'title')
    )

    proposals = TopicProposal.objects.filter(submitted_by=request.user).order_by('-created_at')

    stats = {
        'owned_topics': owned_topics.count(),
        'chapters_created': Chapter.objects.filter(created_by=request.user).count(),
        'topics_published': owned_topics.filter(status='published').count(),
        'topics_pending': owned_topics.filter(status='pending_review').count(),
        'topics_changes': owned_topics.filter(status='changes_requested').count(),
        'proposals_pending': proposals.filter(status='pending_review').count(),
    }

    return render(request, 'accounts/my_lessons.html', {
        'profile': profile,
        'owned_topics': owned_topics,
        'proposals': proposals,
        'stats': stats,
    })


@login_required
def manage_topic_view(request, slug):
    """Topic management page for the topic owner."""
    from learning.models import Topic, Chapter
    from django.db.models import Count

    topic = get_object_or_404(Topic, slug=slug)

    if topic.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not own this topic.')
        return redirect('my_lessons')

    chapters = (
        topic.chapters
        .annotate(lessons_total=Count('lessons', distinct=True))
        .order_by('order', 'title')
    )

    return render(request, 'accounts/manage_topic.html', {
        'topic': topic,
        'chapters': chapters,
    })


@login_required
@require_POST
def request_topic_review_view(request, slug):
    """Contributor submits their topic for staff review."""
    from learning.models import Topic
    topic = get_object_or_404(Topic, slug=slug)

    if topic.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not own this topic.')
        return redirect('my_lessons')

    if topic.status not in ('draft', 'changes_requested'):
        messages.error(request, f'Topic is currently "{topic.get_status_display()}" and cannot be submitted for review.')
        return redirect('manage_topic', slug=topic.slug)

    if not topic.chapters.exists():
        messages.error(request, 'Your topic must have at least one chapter before submitting for review.')
        return redirect('manage_topic', slug=topic.slug)

    has_lessons = topic.chapters.filter(lessons__isnull=False).exists()
    if not has_lessons:
        messages.error(request, 'Your topic must have at least one lesson before submitting for review.')
        return redirect('manage_topic', slug=topic.slug)

    topic.submit_for_review()
    from learning.notifications import notify_topic_review_submitted
    notify_topic_review_submitted(topic)
    messages.success(request, f'"{topic.title}" has been submitted for staff review. You\'ll be notified once it\'s reviewed.')
    return redirect('manage_topic', slug=topic.slug)


@login_required
def create_chapter_view(request, slug):
    """Create a new chapter under an owned topic."""
    from learning.models import Topic, Chapter

    topic = get_object_or_404(Topic, slug=slug)

    if topic.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not own this topic.')
        return redirect('my_lessons')

    if request.method == 'POST':
        form = ChapterCreateForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            base_slug = form.cleaned_data.get('slug') or slugify(title)
            ch_slug = base_slug
            counter = 1
            while Chapter.objects.filter(slug=ch_slug).exists():
                ch_slug = f'{base_slug}-{counter}'
                counter += 1

            chapter = Chapter.objects.create(
                topic=topic,
                title=title,
                slug=ch_slug,
                description=form.cleaned_data['description'],
                meta_title=form.cleaned_data.get('meta_title', ''),
                meta_description=form.cleaned_data.get('meta_description', ''),
                estimated_hours=form.cleaned_data['estimated_hours'],
                order=form.cleaned_data['order'],
                created_by=request.user,
                is_published=False,
            )
            messages.success(request, f'Chapter "{chapter.title}" created. Add lessons to get started.')
            return redirect('manage_chapter', chapter_pk=chapter.pk)
    else:
        form = ChapterCreateForm(initial={'order': topic.chapters.count()})

    return render(request, 'accounts/create_chapter.html', {
        'form': form,
        'topic': topic,
    })


@login_required
def edit_chapter_view(request, chapter_pk):
    """Edit an owned chapter."""
    from learning.models import Chapter

    chapter = get_object_or_404(Chapter, pk=chapter_pk)

    can_edit = (
        chapter.created_by == request.user
        or chapter.topic.owner == request.user
        or request.user.is_staff
    )
    if not can_edit:
        messages.error(request, 'You cannot edit this chapter.')
        return redirect('my_lessons')

    if request.method == 'POST':
        form = ChapterCreateForm(request.POST)
        if form.is_valid():
            chapter.title = form.cleaned_data['title']
            requested_slug = form.cleaned_data.get('slug', '').strip()
            if requested_slug and requested_slug != chapter.slug:
                if Chapter.objects.filter(slug=requested_slug).exclude(pk=chapter.pk).exists():
                    form.add_error('slug', 'That URL slug is already in use.')
                    return render(request, 'accounts/create_chapter.html', {
                        'form': form, 'topic': chapter.topic, 'chapter': chapter, 'editing': True,
                    })
                chapter.slug = requested_slug
            chapter.description = form.cleaned_data['description']
            chapter.meta_title = form.cleaned_data.get('meta_title', '')
            chapter.meta_description = form.cleaned_data.get('meta_description', '')
            chapter.estimated_hours = form.cleaned_data['estimated_hours']
            chapter.order = form.cleaned_data['order']
            chapter.save()
            messages.success(request, f'Chapter "{chapter.title}" updated!')
            return redirect('manage_chapter', chapter_pk=chapter.pk)
    else:
        form = ChapterCreateForm(initial={
            'title': chapter.title,
            'description': chapter.description,
            'slug': chapter.slug,
            'meta_title': chapter.meta_title,
            'meta_description': chapter.meta_description,
            'estimated_hours': chapter.estimated_hours,
            'order': chapter.order,
        })

    return render(request, 'accounts/create_chapter.html', {
        'form': form,
        'topic': chapter.topic,
        'chapter': chapter,
        'editing': True,
    })


@login_required
def manage_chapter_view(request, chapter_pk):
    """Manage a chapter's lessons — for the topic owner."""
    from learning.models import Chapter

    chapter = get_object_or_404(Chapter, pk=chapter_pk)

    can_manage = (
        chapter.topic.owner == request.user
        or chapter.created_by == request.user
        or request.user.is_staff
    )
    if not can_manage:
        messages.error(request, 'You do not have access to this chapter.')
        return redirect('my_lessons')

    lessons = chapter.lessons.order_by('order', 'title')

    return render(request, 'accounts/manage_chapter.html', {
        'chapter': chapter,
        'topic': chapter.topic,
        'lessons': lessons,
    })


@login_required
def create_lesson_for_chapter_view(request, chapter_pk):
    """Create a lesson inside a specific chapter — always saved as draft."""
    from learning.models import Chapter, Lesson

    chapter = get_object_or_404(Chapter, pk=chapter_pk)

    if chapter.topic.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You can only add lessons to chapters in your own topics.')
        return redirect('my_lessons')

    profile, err = _require_contributor(request)
    if err:
        return err

    if request.method == 'POST':
        form = LessonCreateForChapterForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            base_slug = form.cleaned_data.get('slug') or slugify(title)
            lesson_slug = base_slug
            if Lesson.objects.filter(slug=lesson_slug).exists():
                lesson_slug = f'{base_slug}-{uuid.uuid4().hex[:6]}'

            lesson = Lesson.objects.create(
                chapter=chapter,
                title=title,
                slug=lesson_slug,
                summary=form.cleaned_data['summary'],
                meta_title=form.cleaned_data.get('meta_title', ''),
                meta_description=form.cleaned_data.get('meta_description', ''),
                content=form.cleaned_data['content'],
                difficulty=form.cleaned_data['difficulty'],
                video_url=form.cleaned_data.get('video_url', ''),
                reading_time=form.cleaned_data.get('reading_time', 5),
                required_quiz_questions=form.cleaned_data.get('required_quiz_questions') or None,
                order=chapter.lessons.count(),
                is_published=False,
                status='draft',
            )
            messages.success(request, f'Lesson "{title}" saved.')
            return redirect('manage_chapter', chapter_pk=chapter.pk)
    else:
        form = LessonCreateForChapterForm()

    return render(request, 'accounts/create_lesson.html', {
        'form': form,
        'chapter': chapter,
        'topic': chapter.topic,
    })


@login_required
def lesson_edit_view(request, pk):
    from learning.models import Lesson
    lesson = get_object_or_404(Lesson, pk=pk)

    can_edit = (
        lesson.chapter.topic.owner == request.user
        or request.user.is_staff
    )
    if not can_edit:
        messages.error(request, 'You can only edit lessons in your own topics.')
        return redirect('my_lessons')

    if request.method == 'POST':
        form = LessonEditForm(request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.status = 'draft'
            lesson.is_published = False
            messages.success(request, f'Lesson "{lesson.title}" saved.')
            lesson.save()
            return redirect('manage_chapter', chapter_pk=lesson.chapter.pk)
    else:
        form = LessonEditForm(instance=lesson)

    return render(request, 'accounts/lesson_edit.html', {'form': form, 'lesson': lesson})


@login_required
def edit_topic_view(request, slug):
    """Allow topic owner to edit title, description, and icon."""
    from learning.models import Topic
    topic = get_object_or_404(Topic, slug=slug)

    if topic.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You do not own this topic.')
        return redirect('my_lessons')

    if request.method == 'POST':
        form = TopicEditForm(request.POST, request.FILES)
        if form.is_valid():
            new_title = form.cleaned_data['title']
            topic.title = new_title
            topic.description = form.cleaned_data['description']
            topic.icon_html = form.cleaned_data.get('icon_html', '')
            topic.meta_title = form.cleaned_data.get('meta_title', '')
            topic.meta_description = form.cleaned_data.get('meta_description', '')
            topic.image_alt = form.cleaned_data.get('image_alt', '')
            if form.cleaned_data.get('image'):
                topic.image = form.cleaned_data['image']
            topic.save()
            messages.success(request, f'Topic "{topic.title}" updated.')
            return redirect('manage_topic', slug=topic.slug)
    else:
        form = TopicEditForm(initial={
            'title': topic.title,
            'description': topic.description,
            'icon_html': topic.icon_html,
            'meta_title': topic.meta_title,
            'meta_description': topic.meta_description,
            'image_alt': topic.image_alt,
        })

    return render(request, 'accounts/edit_topic.html', {
        'form': form,
        'topic': topic,
    })


@login_required
@require_POST
def move_chapter_view(request, chapter_pk, direction):
    """Move a chapter up or down within its topic."""
    from learning.models import Chapter

    chapter = get_object_or_404(Chapter, pk=chapter_pk)

    can_manage = (
        chapter.topic.owner == request.user
        or request.user.is_staff
    )
    if not can_manage:
        messages.error(request, 'You do not have permission to reorder chapters.')
        return redirect('my_lessons')

    siblings = list(chapter.topic.chapters.order_by('order', 'title'))
    idx = next((i for i, c in enumerate(siblings) if c.pk == chapter.pk), None)

    if direction == 'up' and idx is not None and idx > 0:
        other = siblings[idx - 1]
        chapter.order, other.order = other.order, chapter.order
        if chapter.order == other.order:
            chapter.order = max(0, other.order - 1)
        chapter.save(update_fields=['order'])
        other.save(update_fields=['order'])
    elif direction == 'down' and idx is not None and idx < len(siblings) - 1:
        other = siblings[idx + 1]
        chapter.order, other.order = other.order, chapter.order
        if chapter.order == other.order:
            other.order = chapter.order + 1
        chapter.save(update_fields=['order'])
        other.save(update_fields=['order'])

    return redirect('manage_topic', slug=chapter.topic.slug)


@login_required
@require_POST
def move_lesson_view(request, chapter_pk, lesson_pk, direction):
    """Move a lesson up or down within its chapter."""
    from learning.models import Chapter, Lesson

    chapter = get_object_or_404(Chapter, pk=chapter_pk)
    lesson = get_object_or_404(Lesson, pk=lesson_pk, chapter=chapter)

    can_manage = (
        chapter.topic.owner == request.user
        or chapter.created_by == request.user
        or request.user.is_staff
    )
    if not can_manage:
        messages.error(request, 'You do not have permission to reorder lessons.')
        return redirect('my_lessons')

    siblings = list(chapter.lessons.order_by('order', 'title'))
    idx = next((i for i, l in enumerate(siblings) if l.pk == lesson.pk), None)

    if direction == 'up' and idx is not None and idx > 0:
        other = siblings[idx - 1]
        lesson.order, other.order = other.order, lesson.order
        if lesson.order == other.order:
            lesson.order = max(0, other.order - 1)
        lesson.save(update_fields=['order'])
        other.save(update_fields=['order'])
    elif direction == 'down' and idx is not None and idx < len(siblings) - 1:
        other = siblings[idx + 1]
        lesson.order, other.order = other.order, lesson.order
        if lesson.order == other.order:
            other.order = lesson.order + 1
        lesson.save(update_fields=['order'])
        other.save(update_fields=['order'])

    return redirect('manage_chapter', chapter_pk=chapter.pk)


@login_required
def saved_lessons_view(request):
    from learning.models import LessonBookmark
    bookmarks = (
        LessonBookmark.objects
        .filter(user=request.user)
        .select_related('lesson', 'lesson__chapter', 'lesson__chapter__topic')
        .order_by('-created_at')
    )
    return render(request, 'accounts/saved_lessons.html', {'bookmarks': bookmarks})
