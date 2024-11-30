from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import auth, messages
from myapp.models import *


def user_login(request):
    return redirect('login')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)  # 这里做了登录
            return redirect('home')
        else:
            messages.error(request, '账号或密码错误')
    return render(request, "login.html")


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            messages.error(request, '邮箱已被注册')
            return render(request, 'register.html')
        else:
            if User.objects.filter(username=username).exists():
                messages.error(request, '账号已存在')
                return render(request, 'register.html')
            else:
                user = User.objects.create_user(username=username, password=password, email=email)
                user.save()
                if user:
                    capacity = request.POST.get('capacity')
                    user_capacity = USER_TO_CAPACITY.objects.create(user=user, capacity=capacity)
                    user_capacity.save()
                    messages.success(request, '注册成功！')
                    return redirect('login')
    return render(request, 'register.html')


# todo:根据不同的用户跳转到不同的起始页面
def home(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('login')  # 未登录用户跳转到登录页面
    try:
        # 查询用户的身份
        user_capacity = USER_TO_CAPACITY.objects.get(username=user)
        capacity = user_capacity.capacity

        # 根据身份跳转到不同页面
        if capacity == 3:  # 管理员
            return redirect('admin_home')
        else:              #学生和教师
            return redirect('user_home')

    except USER_TO_CAPACITY.DoesNotExist:
        # 如果用户未绑定身份，则跳转到错误页面并传递错误原因
        error_reason = "user_not_bound"

        return redirect(f'error_page?reason={error_reason}')


def error_page(request):
    reason = request.GET.get('reason', 'unknown')           #默认值unknown
    if reason == 'user_not_bound':
        error_message = "用户未绑定身份，请联系管理员。"
    else:
        error_message = "发生未知错误。"
    return render(request, 'error_page.html', {'error_message': error_message})


@login_required
def user_home(request):
    user = request.user  # 获取当前登录用户

    # 获取用户身份
    try:
        user_capacity = USER_TO_CAPACITY.objects.get(username=user).capacity
    except USER_TO_CAPACITY.DoesNotExist:
        # 如果未绑定身份，跳转到错误页面或显示默认信息
        return render(request, 'error_page.html', {'error_message': "用户未绑定身份。"})

    # 根据用户身份获取相关课程
    if user_capacity == 1:  # 学生身份
        classes = Class.objects.filter(students=user)  # 获取学生加入的课程
    elif user_capacity == 2:  # 教师身份
        classes = Class.objects.filter(teacher=user)  # 获取教师教授的课程
    else:  # 管理员身份
        classes = Class.objects.all()  # 管理员查看所有课程

    # 将课程信息传递到模板
    return render(request, 'user_home.html', {
        'classes': classes,
        'user_capacity': dict(USER_TO_CAPACITY.CAPACITY_CHOICES).get(user_capacity, "未知")
    })


def admin_home(request):
    pass


def error_page(request):
    pass


def stu_class(request):  ##学生点击特定课程后触发
    pass


def send_emoji(request):  ##学生点击发送表情后触发
    pass


def emoji_history(request):  ##学生点击查询课程历史表情后触发
    pass


def th_class(request):  ##教师点击特定课程后触发
    pass


def add_stu(request):  ##教师为特定课程添加学生
    pass


def del_stu(request):  ##教师/管理员将某学生从课程中移除
    pass


def view_all(request):  ##教师查看某课程的统计信息
    pass


def export_to_xxx(request):  ##课程信息导出
    pass


def adm_user(request):  ##管理员查看用户数据的统计
    pass


def adm_add_user(request):  ##管理员可增加用户
    pass


def adm_del_user(request):  ##管理员可删除用户
    pass


def adm_class(request):  ##管理员点击某课程
    pass


def adm_del_msg(request):  # 管理员有权限删除消息
    pass


def adm_add_class(request):  # 管理员有权限增删课程
    pass


def adm_del_class(request):
    pass

# emoji管理暂定
