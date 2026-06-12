from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.db.models import Count, Q, Prefetch
from .models import Topic, Chapter, Lesson


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
        return ctx
