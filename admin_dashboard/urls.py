from django.urls import path
from . import views
from .views import add_milk_collection
app_name = 'admin_dashboard'

urlpatterns = [
    path('manage_users', views.manage_users, name='manage_users'),  # Default dashboard for managing users
    path('users/<int:user_id>/view/', views.view_user, name='view_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
    path('users/<int:user_id>/activate/', views.activate_user, name='activate_user'),
    # milk collection and overview
 # View current milk & commission rates (Admin + All)
     path('rates/manage/', views.manage_rates, name='manage_rates'),


    # Collect milk from farmer (Admin + Collector)
    path('milk-collections/add/', add_milk_collection, name='add_milk_collection'),


    # View list of milk collections (Admin + Collector + Farmer)
    path('milk-collections/', views.milk_collection_list, name='milk_collection_list'),
    path('milk-collections/<int:pk>/', views.milk_collection_detail, name='milk_collection_detail'),
    path('milk-collections/<int:pk>/edit/', views.edit_milk_collection, name='edit_milk_collection'),
    path('milk-collections/<int:pk>/delete/', views.delete_milk_collection, name='delete_milk_collection'),
    path('milk-summary/', views.milk_summary_view, name='milk_summary'),

# Milk rate
 
    



    # Make payment (Admin only)

path('payments/overview/', views.payment_overview, name='payment_overview'),
    path('payments/farmers/', views.farmer_payments_list, name='farmer_payments'),
    path('payments/farmers/<int:farmer_id>/', views.farmer_payment_detail, name='farmer_payment_detail'),
    path('payments/collectors/', views.collector_payments_list, name='collector_payments_list'),
    path('payments/collectors/<int:collector_id>/', views.collector_payment_detail, name='collector_payment_detail'),
     path('payments/batch-update/', views.batch_update_payments, name='batch_update_payments'),

path('payments/generate/', views.generate_payments, name='generate_payments'),

# INVENTORY MANAGEMENT
    path("inventory/", views.supplement_list, name="supplement_list"),
    path("inventory/add/", views.supplement_add, name="add_supplement"),
    path("inventory/edit/<int:pk>/", views.supplement_edit, name="edit_supplement"),
    path("inventory/delete/<int:pk>/", views.supplement_delete, name="delete_supplement"),

    # Supplement Orders
    path("inventory/orders/", views.supplement_orders, name="supplement_orders"),
    path("inventory/orders/<int:pk>/", views.supplement_order_detail, name="supplement_order_detail"),
    path("inventory/orders/<int:pk>/mark-paid/", views.mark_order_paid, name="mark_order_paid"),
    
    # ANALYTICS
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),



]
