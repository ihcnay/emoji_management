from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import auth, messages
from .models import USER_TO_CAPACITY


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


def home(request):
    username = request.user.username
    return render(request, 'home.html', {'username': username})


def send_page(request):             ##转到发送界面，可选择表情和课堂号等
    pass


def send_emoji(request):            ##
    pass


def history_page(request):           ##历史查询页面，根据课堂号查询历史表情
    pass


def view_history(request):
    pass


def export_page(request):             ##导出数据界面，选择导出方式
    pass


def export_to_xxx(request):
    pass
