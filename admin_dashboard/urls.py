from django.urls import path
from . import views
from .views import collector_payment_history
app_name = 'admin_dashboard'

urlpatterns = [
    path('manage_users', views.manage_users, name='manage_users'),  # Default dashboard for managing users
    path('users/<int:user_id>/view/', views.view_user, name='view_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
    path('users/<int:user_id>/activate/', views.activate_user, name='activate_user'),
    # milk collection and overview
    path('milk/', views.milk_overview, name='milk_overview'),
    path('milk/farmer-summary/', views.farmer_summary, name='farmer_summary'), 
    path('milk/create/', views.create_milk, name='milk_create'),
    path('milk/edit/<int:pk>/', views.edit_milk, name='milk_edit'),
    path('milk/delete/<int:pk>/', views.delete_milk, name='milk_delete'),
    # PAYMENT URL
    path('payments/new/', views.record_payment, name='record_payment'),
    path('payments/collector/<int:user_id>/', views.collector_payment_history, name='collector_payment_history'),
    path('payments/farmer/<int:user_id>/', views.farmer_payment_history, name='farmer_payment_history'),
    path('payments/rates/', views.rate_settings_view, name='rate_settings'),
    path('collectors/', views.collector_list, name='collector_list'),
    path('farmers/', views.farmer_list, name='farmer_list'),

]
