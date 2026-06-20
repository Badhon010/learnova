from django.urls import path
from . import views

urlpatterns = [
    path('topics/', views.TopicsView.as_view(), name='topics'),
    path('topics/<slug:slug>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('topics/<slug:topic_slug>/chapters/<slug:chapter_slug>/', views.ChapterDetailView.as_view(), name='chapter_detail'),
    path('lessons/<slug:slug>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('lessons/<slug:slug>/bookmark/', views.bookmark_toggle_view, name='lesson_bookmark'),
    path('lessons/<slug:slug>/comment/', views.add_comment_view, name='add_comment'),
    path('lessons/<slug:slug>/rate/', views.rate_lesson_view, name='rate_lesson'),
    path('comments/<int:pk>/delete/', views.delete_comment_view, name='delete_comment'),
    path('comments/<int:comment_pk>/reply/', views.add_reply_view, name='add_reply'),
    path('replies/<int:pk>/delete/', views.delete_reply_view, name='delete_reply'),
    path('certificates/<uuid:certificate_id>/', views.certificate_view, name='certificate_view'),
    path('certificates/<uuid:certificate_id>/verify/', views.certificate_verify_view, name='certificate_verify'),
    path('api/progress/', views.update_progress_view, name='update_progress'),
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view, name='notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read_view, name='notifications_mark_all_read'),
    path('api/notifications/count/', views.notifications_unread_count_view, name='notifications_count'),
    path('api/notifications/recent/', views.notifications_recent_api_view, name='notifications_recent'),
    # Topic Proposals
    path('proposals/submit/', views.submit_topic_proposal_view, name='submit_topic_proposal'),
    path('proposals/', views.my_proposals_view, name='my_proposals'),
    path('proposals/<int:pk>/edit/', views.edit_proposal_view, name='edit_proposal'),
    path('proposals/<int:pk>/delete/', views.delete_proposal_view, name='delete_proposal'),
    # Staff review queue
    path('review/', views.staff_review_queue_view, name='staff_review_queue'),
    path('review/topics/<int:pk>/', views.staff_review_topic_view, name='staff_review_topic'),
    path('review/proposals/<int:pk>/approve/', views.staff_approve_proposal_view, name='staff_approve_proposal'),
    path('review/proposals/<int:pk>/reject/', views.staff_reject_proposal_view, name='staff_reject_proposal'),
]
