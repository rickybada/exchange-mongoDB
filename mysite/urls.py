from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home.html'),
    path('admin/', admin.site.urls),
    path('exchange/', include('exchange.urls')),
]
