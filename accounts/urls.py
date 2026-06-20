from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/<str:username>/', views.profile_detail_view, name='profile_detail'),
    path('my-lessons/', views.my_lessons_view, name='my_lessons'),
    path('lesson/<int:pk>/edit/', views.lesson_edit_view, name='lesson_edit'),
    path('saved/', views.saved_lessons_view, name='saved_lessons'),
    # Topic ownership workflow
    path('topics/<slug:slug>/manage/', views.manage_topic_view, name='manage_topic'),
    path('topics/<slug:slug>/chapters/create/', views.create_chapter_view, name='create_chapter'),
    path('topics/<slug:slug>/request-review/', views.request_topic_review_view, name='request_topic_review'),
    path('chapters/<int:chapter_pk>/edit/', views.edit_chapter_view, name='edit_chapter'),
    path('chapters/<int:chapter_pk>/manage/', views.manage_chapter_view, name='manage_chapter'),
    path('chapters/<int:chapter_pk>/lessons/create/', views.create_lesson_for_chapter_view, name='create_lesson_for_chapter'),
    path('topics/<slug:slug>/edit/', views.edit_topic_view, name='edit_topic'),
    # Ordering
    path('chapters/<int:chapter_pk>/move/<str:direction>/', views.move_chapter_view, name='move_chapter'),
    path('chapters/<int:chapter_pk>/lessons/<int:lesson_pk>/move/<str:direction>/', views.move_lesson_view, name='move_lesson'),
]
