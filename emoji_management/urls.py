from django.urls import path
from myapp import views

urlpatterns = [
    path('', views.user_login, name='start'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('home', views.home, name='home'),
    path('user_home',views.user_home,name='user_home'),
    path('course/<int:course_id>/', views.user_class, name='course_detail'),
]
