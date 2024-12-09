from django.urls import path
from myapp import views

urlpatterns = [
    path('', views.user_login, name='start'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('home', views.home, name='home'),
    path('user_home',views.user_home,name='user_home'),
    path('course/<str:classid>/', views.course_detail, name='course_detail'),
    path('add_course_ajax/', views.add_course_ajax, name='add_course_ajax'),
    path('course/<str:classid>/send_message/', views.send_message_ajax, name='send_message_ajax'),
    path('add_student/', views.add_student, name='add_student'),
    path('api/get_students_in_course/', views.get_students_in_course, name='get_students_in_course'),
    path('api/remove_student_from_course/', views.remove_student_from_course, name='remove_student_from_course'),
]
