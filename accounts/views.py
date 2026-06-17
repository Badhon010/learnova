from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.text import slugify
from django.http import Http404
import uuid

from .forms import RegisterForm, LoginForm, ProfileEditForm, LessonSubmitForm, LessonEditForm
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
    from learning.models import Topic, Lesson, UserLessonProgress, LessonBookmark, RecentlyViewed
    from quizzes.models import QuizAttempt

    profile = request.user.profile

    # Learning stats
    progress_qs = UserLessonProgress.objects.filter(user=request.user)
    lessons_started = progress_qs.count()
    lessons_completed = progress_qs.filter(is_complete=True).count()

    # Continue learning (last 5 recently viewed with progress)
    recently_viewed = (
        RecentlyViewed.objects
        .filter(user=request.user)
        .select_related('lesson', 'lesson__chapter', 'lesson__chapter__topic')
        .order_by('-viewed_at')[:10]
    )

    continue_learning = []
    for rv in recently_viewed[:5]:
        prog = progress_qs.filter(lesson=rv.lesson).first()
        continue_learning.append({
            'lesson': rv.lesson,
            'progress': prog.progress_pct if prog else 0,
            'is_complete': prog.is_complete if prog else False,
        })

    # Bookmarks (last 5)
    bookmarks = (
        LessonBookmark.objects
        .filter(user=request.user)
        .select_related('lesson', 'lesson__chapter', 'lesson__chapter__topic')
        .order_by('-created_at')[:5]
    )

    # Quiz stats
    quiz_attempts = QuizAttempt.objects.filter(user=request.user)
    quizzes_completed = quiz_attempts.count()
    avg_score = 0
    if quizzes_completed:
        total_score = sum(a.score for a in quiz_attempts)
        avg_score = round(total_score / quizzes_completed)

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
        .filter(submitted_by=user, is_published=True, status='published')
        .select_related('chapter', 'chapter__topic')
        .order_by('-published_at')
    )

    return render(request, 'accounts/profile_detail.html', {
        'profile_user': user,
        'profile': profile,
        'published_lessons': published_lessons,
    })


@login_required
def submit_lesson_view(request):
    profile = request.user.profile
    if not profile.is_contributor:
        messages.error(request, 'Only contributors can submit lessons. Contact an admin to upgrade your role.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = LessonSubmitForm(request.POST)
        action = request.POST.get('action', 'submit')
        if form.is_valid():
            from learning.models import Lesson
            from django.utils import timezone
            title = form.cleaned_data['title']
            base_slug = slugify(title)
            slug = base_slug
            if Lesson.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{uuid.uuid4().hex[:6]}'

            status = 'pending_review' if action == 'submit' else 'draft'
            is_published = False

            lesson = Lesson.objects.create(
                chapter=form.cleaned_data['chapter'],
                title=title,
                slug=slug,
                summary=form.cleaned_data['summary'],
                content=form.cleaned_data['content'],
                difficulty=form.cleaned_data['difficulty'],
                video_url=form.cleaned_data.get('video_url', ''),
                reading_time=form.cleaned_data.get('reading_time', 5),
                is_published=is_published,
                status=status,
                submitted_by=request.user,
            )
            if action == 'submit':
                messages.success(request, f'Your lesson "{title}" was submitted for review.')
            else:
                messages.success(request, f'Lesson "{title}" saved as draft.')
            return redirect('my_lessons')
    else:
        form = LessonSubmitForm()

    return render(request, 'accounts/submit_lesson.html', {'form': form})


@login_required
def my_lessons_view(request):
    profile = request.user.profile
    if not profile.is_contributor:
        messages.error(request, 'Only contributors can access the lesson dashboard.')
        return redirect('dashboard')

    from learning.models import Lesson
    lessons = Lesson.objects.filter(submitted_by=request.user).order_by('-updated_at')

    drafts = [l for l in lessons if l.status == 'draft']
    pending = [l for l in lessons if l.status == 'pending_review']
    published = [l for l in lessons if l.status == 'published']
    rejected = [l for l in lessons if l.status == 'rejected']

    return render(request, 'accounts/my_lessons.html', {
        'profile': profile,
        'drafts': drafts,
        'pending': pending,
        'published': published,
        'rejected': rejected,
    })


@login_required
def lesson_edit_view(request, pk):
    from learning.models import Lesson
    lesson = get_object_or_404(Lesson, pk=pk)

    if lesson.submitted_by != request.user:
        messages.error(request, 'You can only edit your own lessons.')
        return redirect('my_lessons')

    if lesson.status not in ('draft', 'rejected'):
        messages.error(request, 'Only draft or rejected lessons can be edited.')
        return redirect('my_lessons')

    if request.method == 'POST':
        form = LessonEditForm(request.POST, instance=lesson)
        action = request.POST.get('action', 'save')
        if form.is_valid():
            lesson = form.save(commit=False)
            if action == 'submit':
                lesson.status = 'pending_review'
                lesson.rejection_note = ''
                messages.success(request, f'Lesson "{lesson.title}" submitted for review.')
            else:
                lesson.status = 'draft'
                messages.success(request, f'Lesson "{lesson.title}" saved as draft.')
            lesson.save()
            return redirect('my_lessons')
    else:
        form = LessonEditForm(instance=lesson)

    return render(request, 'accounts/lesson_edit.html', {'form': form, 'lesson': lesson})


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
