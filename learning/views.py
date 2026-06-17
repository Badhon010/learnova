from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
import json

from .models import Topic, Chapter, Lesson, LessonBookmark, UserLessonProgress, RecentlyViewed


def _published_topics():
    """Annotated queryset — eliminates N+1 for chapter/lesson counts."""
    return Topic.objects.filter(is_published=True).annotate(
        num_chapters=Count(
            'chapters',
            filter=Q(chapters__is_published=True),
            distinct=True,
        ),
        num_lessons=Count(
            'chapters__lessons',
            filter=Q(
                chapters__is_published=True,
                chapters__lessons__is_published=True,
            ),
            distinct=True,
        ),
    )


def _published_lessons_prefetch():
    return Prefetch(
        'lessons',
        queryset=Lesson.objects.filter(is_published=True).order_by('order'),
    )


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
            .annotate(
                num_lessons=Count(
                    'lessons',
                    filter=Q(lessons__is_published=True),
                    distinct=True,
                )
            )
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
            .annotate(
                num_lessons=Count(
                    'lessons',
                    filter=Q(lessons__is_published=True),
                    distinct=True,
                )
            )
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
            .annotate(
                num_lessons=Count(
                    'lessons',
                    filter=Q(lessons__is_published=True),
                    distinct=True,
                )
            )
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
        return Lesson.objects.filter(is_published=True).select_related(
            'chapter', 'chapter__topic'
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
            (i for i, l in enumerate(all_topic_lessons) if l.id == lesson.id),
            None,
        )

        ctx['chapter'] = chapter
        ctx['topic'] = topic
        ctx['all_chapters'] = all_chapters
        ctx['chapter_lessons'] = list(chapter.lessons.filter(is_published=True).order_by('order'))
        ctx['prev_lesson'] = (
            all_topic_lessons[current_idx - 1]
            if current_idx and current_idx > 0 else None
        )
        ctx['next_lesson'] = (
            all_topic_lessons[current_idx + 1]
            if current_idx is not None and current_idx < len(all_topic_lessons) - 1
            else None
        )
        ctx['lesson_position'] = (current_idx + 1) if current_idx is not None else 1
        ctx['lesson_total'] = len(all_topic_lessons)
        ctx['breadcrumbs'] = [
            {'label': 'Topics', 'url': reverse('topics')},
            {'label': topic.title, 'url': topic.get_absolute_url()},
            {'label': chapter.title, 'url': chapter.get_absolute_url()},
            {'label': lesson.title, 'url': None},
        ]

        # Quiz
        try:
            ctx['quiz'] = lesson.quiz
        except Exception:
            ctx['quiz'] = None

        # Bookmark + progress for authenticated users
        if self.request.user.is_authenticated:
            ctx['is_bookmarked'] = LessonBookmark.objects.filter(
                user=self.request.user, lesson=lesson
            ).exists()
            progress = UserLessonProgress.objects.filter(
                user=self.request.user, lesson=lesson
            ).first()
            ctx['user_progress'] = progress

            # Update RecentlyViewed
            RecentlyViewed.objects.update_or_create(
                user=self.request.user, lesson=lesson,
                defaults={},
            )

            # Best quiz attempt
            if ctx['quiz']:
                from quizzes.models import QuizAttempt
                ctx['best_attempt'] = QuizAttempt.objects.filter(
                    user=self.request.user, quiz=ctx['quiz']
                ).order_by('-score').first()
            else:
                ctx['best_attempt'] = None
        else:
            ctx['is_bookmarked'] = False
            ctx['user_progress'] = None
            ctx['best_attempt'] = None

        return ctx


@login_required
@require_POST
@csrf_protect
def bookmark_toggle_view(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug, is_published=True)
    bookmark, created = LessonBookmark.objects.get_or_create(
        user=request.user, lesson=lesson
    )
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True
    return JsonResponse({'bookmarked': bookmarked})


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

    progress_obj, _ = UserLessonProgress.objects.update_or_create(
        user=request.user, lesson=lesson,
        defaults={
            'progress_pct': progress_pct,
            'is_complete': progress_pct >= 100,
        },
    )

    RecentlyViewed.objects.update_or_create(
        user=request.user, lesson=lesson,
        defaults={},
    )

    return JsonResponse({'ok': True, 'progress': progress_pct})
