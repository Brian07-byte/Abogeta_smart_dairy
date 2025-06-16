from django.urls import path
from . import views
from .views import read_notification

urlpatterns = [
    path('', views.home_redirect, name='home'),  # ✅ This is required
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
     path('dashboard/admin/', views.dashboard_view, name='admin_dashboard'),
    path('dashboard/farmer/', views.farmer_dashboard, name='farmer_dashboard'),
    path('dashboard/collector/', views.collector_dashboard, name='collector_dashboard'),


    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    path('notification/read/<int:pk>/', read_notification, name='read_notification'),
    
    # feedback
    path('feedback/send/', views.send_feedback, name='send_feedback'),
    path('feedback/inbox/', views.inbox, name='inbox'),
    path('feedback/<int:pk>/', views.feedback_detail, name='feedback_detail'),
]
