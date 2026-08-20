import json
import logging

from django.views.generic import TemplateView, FormView
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.conf import settings
from django import forms
from django.db.models import Count, Q

from learning.models import Topic, Chapter, Lesson
from .models import NewsletterSubscriber, ContactMessage


logger = logging.getLogger(__name__)


def _annotated_topics():
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


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        featured_topics = _annotated_topics().filter(featured=True).order_by('order')[:6]
        if not featured_topics:
            featured_topics = _annotated_topics().order_by('order')[:6]

        featured_lessons = (
            Lesson.objects
            .filter(
                is_published=True,
                featured=True,
                chapter__is_published=True,
                chapter__topic__is_published=True,
            )
            .select_related('chapter', 'chapter__topic')
            .order_by('chapter__topic__order', 'chapter__order', 'order')[:6]
        )
        if not featured_lessons:
            featured_lessons = (
                Lesson.objects
                .filter(
                    is_published=True,
                    chapter__is_published=True,
                    chapter__topic__is_published=True,
                )
                .select_related('chapter', 'chapter__topic')[:6]
            )

        ctx['featured_topics'] = featured_topics
        ctx['popular_lessons'] = featured_lessons
        ctx['topic_count'] = Topic.objects.filter(is_published=True).count()
        ctx['lesson_count'] = Lesson.objects.filter(
            is_published=True,
            chapter__is_published=True,
            chapter__topic__is_published=True,
        ).count()
        ctx['subscriber_count'] = NewsletterSubscriber.objects.filter(is_active=True).count()
        return ctx


class AboutView(TemplateView):
    template_name = 'core/about.html'


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Your name'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'How can we help?'}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Your message...', 'rows': 5}),
    )


class ContactView(FormView):
    template_name = 'core/contact.html'
    form_class = ContactForm
    success_url = '/contact/'

    def form_valid(self, form):
        data = form.cleaned_data
        ContactMessage.objects.create(
            name=data['name'],
            email=data['email'],
            subject=data['subject'],
            message=data['message'],
        )
        body = (
            f'New contact message via Learnova\n\n'
            f"Name:    {data['name']}\n"
            f"Email:   {data['email']}\n"
            f"Subject: {data['subject']}\n\n"
            f"Message:\n{data['message']}\n"
        )
        recipient = getattr(settings, 'CONTACT_EMAIL', '') or getattr(settings, 'EMAIL_HOST_USER', '')
        if recipient:
            try:
                send_mail(
                    subject=f"[Learnova Contact] {data['subject']}",
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )
            except Exception:
                logger.exception('Contact email could not be sent for message %s', data['subject'])
        return render(
            self.request,
            self.template_name,
            {'form': ContactForm(), 'success': True},
        )


@csrf_protect
@require_POST
def newsletter_subscribe(request):
    try:
        payload = json.loads(request.body)
        email = (payload.get('email') or '').strip().lower()
    except (ValueError, AttributeError):
        email = request.POST.get('email', '').strip().lower()

    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return JsonResponse({'ok': False, 'error': 'Please enter a valid email address.'}, status=400)

    obj, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={'is_active': True},
    )
    if not created and not obj.is_active:
        obj.is_active = True
        obj.save()
        created = True

    if created:
        try:
            send_mail(
                subject='Welcome to Learnova!',
                message=(
                    f'Hi there,\n\n'
                    f'Thank you for subscribing to the Learnova newsletter!\n\n'
                    f'You\'ll receive the latest tutorials, code examples, and learning '
                    f'resources straight to your inbox.\n\n'
                    f'Happy learning,\nThe Learnova Team\n'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            logger.exception('Newsletter welcome email could not be sent to %s', email)

    return JsonResponse({'ok': True, 'already': not created})


def search_suggestions_view(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    results = []

    topics = Topic.objects.filter(
        is_published=True,
    ).filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    )[:3]
    for t in topics:
        results.append({
            'type': 'topic',
            'title': t.title,
            'url': t.get_absolute_url(),
            'meta': t.description[:80] + '…' if len(t.description) > 80 else t.description,
        })

    chapters = Chapter.objects.filter(
        is_published=True,
    ).filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ).select_related('topic')[:2]
    for c in chapters:
        results.append({
            'type': 'chapter',
            'title': c.title,
            'url': c.get_absolute_url(),
            'meta': c.topic.title,
        })

    lessons = Lesson.objects.filter(
        is_published=True,
        chapter__is_published=True,
        chapter__topic__is_published=True,
    ).filter(
        Q(title__icontains=query) | Q(summary__icontains=query)
    ).select_related('chapter', 'chapter__topic')[:5]
    for l in lessons:
        results.append({
            'type': 'lesson',
            'title': l.title,
            'url': l.get_absolute_url(),
            'meta': l.chapter.topic.title + ' / ' + l.chapter.title,
        })

    return JsonResponse({'results': results[:8]})


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
