from django.urls import path
from myapp import views

urlpatterns = [
    path('', views.user_login, name='start'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('home', views.home, name='home'),
    path('user_home',views.user_home,name='user_home'),
    path('admin_home',views.admin_home,name='admin_home'),
    path('course/<str:classid>/', views.course_detail, name='course_detail'),
    path('add_course_ajax/', views.add_course_ajax, name='add_course_ajax'),
    path('course/<str:classid>/send_message/', views.send_message_ajax, name='send_message_ajax'),
    path('add_student/', views.add_student, name='add_student'),
    path('get_students_in_course/', views.get_students_in_course, name='get_students_in_course'),
    path('remove_student_from_course/', views.remove_student_from_course, name='remove_student_from_course'),
    path('edit_teacher/<int:classid>/', views.edit_teacher, name='edit_teacher'),  # 修改教师接口
    path('manage_emoji/', views.manage_emoji, name='manage_emoji'),
    path('remove_course/<str:classid>/', views.remove_course, name='remove_course'),
    path('admin_class_detail/<str:classid>/', views.admin_class_detail, name='admin_class_detail'),
    path('delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('add_user/',views.add_user, name='add_user'),
    path('delete_user/', views.delete_user, name='delete_user'),
]
