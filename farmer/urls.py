from django.urls import path
from . import views

urlpatterns = [
    
    path('milk-history/', views.milk_history, name='milk_history'),
    path('milk-history/<int:record_id>/', views.milk_detail, name='milk_detail'),
#     payments
path('my-payments/', views.my_payments_view, name='my_payments'),
path('payment/<int:payment_id>/milk-records/', views.view_milk_for_payment, name='view_milk_for_payment'),

# SUPPLEMENTS
path('supplements/', views.supplement_list, name='supplement_list'),
path('supplements/<int:supplement_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
path('cart/', views.view_cart, name='view_cart'),
path('cart/increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
path('cart/decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
path('cart/delete/<int:item_id>/', views.delete_cart_item, name='delete_cart_item'),
path('cart/clear/', views.clear_cart, name='clear_cart'),

# CHECKOUT
path('checkout/', views.checkout_view, name='checkout'),
path('order-summary/', views.order_summary_view, name='order_summary'),
 path('orders/', views.order_list_view, name='order_list'),

# FEEDBACK
path('feedback/submit/', views.submit_feedback_view, name='submit_feedback'),
    path('feedback/sent/', views.feedback_sent_view, name='feedback_sent'),
    path('feedback/received/', views.feedback_received_view, name='feedback_received'),
    path('feedback/reply/<int:feedback_id>/', views.feedback_reply_view, name='feedback_reply'),

]
