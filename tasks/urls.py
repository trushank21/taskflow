from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/edit/', views.edit_comment, name='comment_edit'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='comment_delete'),
    path('tasks/<int:pk>/status/', views.update_task_status, name='update_status'),
    path('tasks/<int:pk>/progress/', views.update_progress, name='update_progress'),
    path('task/<int:pk>/attach/', views.add_attachment, name='add_attachment'),
    path('attachment/<int:pk>/delete/', views.delete_attachment, name='delete_attachment'),
    path('attachment/<int:pk>/download/', views.download_attachment, name='download_attachment'),
    path('tasks/<int:pk>/clear-history/', views.clear_task_history, name='clear_history'),
    # path('update-status/<int:pk>/', views.update_task_status, name='update_task_status'),
]


