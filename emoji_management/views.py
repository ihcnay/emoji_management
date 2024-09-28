from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import auth, messages


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
                    messages.success(request, '注册成功！')
                    return redirect('login')
    return render(request, 'register.html')


def home(request):
    username = request.user.username
    return render(request, 'home.html', {'username': username})
