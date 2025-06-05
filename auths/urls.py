from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('collector/dashboard/', views.collector_dashboard, name='collector_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
