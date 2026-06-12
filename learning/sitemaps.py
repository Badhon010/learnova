from django.contrib.sitemaps import Sitemap
from .models import Topic, Chapter, Lesson


class TopicSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Topic.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class ChapterSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Chapter.objects.filter(is_published=True, topic__is_published=True).select_related('topic')

    def lastmod(self, obj):
        return obj.updated_at


class LessonSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.9

    def items(self):
        return Lesson.objects.filter(
            is_published=True,
            chapter__is_published=True,
            chapter__topic__is_published=True,
        ).select_related('chapter', 'chapter__topic')

    def lastmod(self, obj):
        return obj.updated_at
