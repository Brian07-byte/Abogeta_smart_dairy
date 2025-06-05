from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('manage_users', views.manage_users, name='manage_users'),  # Default dashboard for managing users
    path('users/<int:user_id>/view/', views.view_user, name='view_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
    path('users/<int:user_id>/activate/', views.activate_user, name='activate_user'),
]
