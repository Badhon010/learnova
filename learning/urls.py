from django.urls import path
from . import views

urlpatterns = [
    path('topics/', views.TopicsView.as_view(), name='topics'),
    path('topics/<slug:slug>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('topics/<slug:topic_slug>/chapters/<slug:chapter_slug>/', views.ChapterDetailView.as_view(), name='chapter_detail'),
    path('lessons/<slug:slug>/', views.LessonDetailView.as_view(), name='lesson_detail'),
]
