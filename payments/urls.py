from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initialize/', views.initialize_payment, name='initialize_payment'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('webhook/', views.paystack_webhook, name='paystack_webhook'),
]
