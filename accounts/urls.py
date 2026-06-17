from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/<str:username>/', views.profile_detail_view, name='profile_detail'),
    path('submit-lesson/', views.submit_lesson_view, name='submit_lesson'),
    path('my-lessons/', views.my_lessons_view, name='my_lessons'),
    path('lesson/<int:pk>/edit/', views.lesson_edit_view, name='lesson_edit'),
    path('saved/', views.saved_lessons_view, name='saved_lessons'),
]
