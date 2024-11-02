from django.urls import path
from myapp import views

urlpatterns = [
    path('', views.user_login, name='start'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('home', views.home, name='home')
]
