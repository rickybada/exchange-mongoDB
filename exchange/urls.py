from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('registration/', views.registration_view, name='registration'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('order_json/', views.order_json_view, name='order_json'),
    path('buy_sell/', views.buy_sell_view, name='buy_sell'),
]
