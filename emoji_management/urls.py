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
    path('api/get_students_in_course/', views.get_students_in_course, name='get_students_in_course'),
    path('api/remove_student_from_course/', views.remove_student_from_course, name='remove_student_from_course'),
    # 教师功能
    path('teacher/view_all/', views.view_all, name='teacher_view_all'),
    path('teacher/export/', views.export_to_xxx, name='teacher_export'),
    # 管理员功能
    path('admin/user/', views.adm_user, name='adm_user_stats'),
    path('admin/add_user/', views.adm_add_user, name='adm_add_user'),
    path('admin/del_user/', views.adm_del_user, name='adm_del_user'),
    path('admin/class/', views.adm_class, name='adm_class_detail'),
    path('admin/del_msg/', views.adm_del_msg, name='adm_del_msg'),
    path('admin/add_class/', views.adm_add_class, name='adm_add_class'),
    path('admin/del_class/', views.adm_del_class, name='adm_del_class'),
]