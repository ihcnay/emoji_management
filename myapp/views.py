from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib import auth, messages
from myapp.models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            user_role = request.POST['user_role']
            admin_sequence = request.POST.get('admin_sequence', None)  # 获取管理员序列号，默认为 None

            # 验证管理员序列号
            if user_role == 'admin':
                if admin_sequence != '123456':  # 替换为实际序列号
                    messages.error(request, '无效的管理员序列号！')
                    return render(request, 'register.html')

            # 检查邮箱是否已被注册
            if User.objects.filter(email=email).exists():
                messages.error(request, '邮箱已被注册')
                return render(request, 'register.html')

            # 检查用户名是否已存在
            if User.objects.filter(username=username).exists():
                messages.error(request, '账号已存在')
                return render(request, 'register.html')

            # 确定用户身份
            if user_role == 'student':
                capacity = 1
            elif user_role == 'teacher':
                capacity = 2
            elif user_role == 'admin':
                capacity = 3
            else:
                messages.error(request, '无效的用户角色选择')
                return render(request, 'register.html')
            # 创建用户
            user = User.objects.create_user(username=username, password=password, email=email)
            USER_TO_CAPACITY.objects.create(username=user, capacity=capacity)
            messages.success(request, '注册成功！')
            return redirect('login')

        except Exception as e:
            # 记录异常和回溯信息
            messages.error(request, f'发生错误，请稍后再试: {str(e)}')
            return render(request, 'register.html')

    return render(request, 'register.html')


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
        error_reason = "user_not_found"

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
        classes = user.student_classes.all()  # 获取学生加入的课程
    elif user_capacity == 2:  # 教师身份
        classes = user.teacher_classes.all()  # 获取教师教授的课程
    else:
        classes = []  # 未知身份不显示课程

    # 将课程信息和教师标识传递到模板
    return render(request, 'user_home.html', {
        'classes': classes,
        'is_teacher': user_capacity == 2,  # 标识是否为教师
        'user_capacity': dict(USER_TO_CAPACITY.CAPACITY_CHOICES).get(user_capacity, "未知"),
    })


@login_required
def admin_home(request):
    # 检查用户是否为管理员
    user = request.user
    try:
        user_capacity = USER_TO_CAPACITY.objects.get(username=user).capacity
    except USER_TO_CAPACITY.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': "用户未绑定身份。"})

    if user_capacity != 3:  # 如果不是管理员，跳转到错误页面
        return render(request, 'error_page.html', {'error_message': "无权限访问该页面。"})

    # 查询所有课程信息
    all_classes = Class.objects.all()

    # 统计课程总数和学生人数等信息（可选）
    class_stats = []
    for cls in all_classes:
        student_count = cls.students.count()  # Class 模型有一个 ManyToManyField 关联到学生
        class_stats.append({
            'class': cls,
            'student_count': student_count,
        })

    # 将所有课程信息传递到模板
    return render(request, 'admin_home.html', {
        'all_classes': all_classes,
        'class_stats': class_stats,
        'total_classes': all_classes.count(),
    })


def error_page(request):
    pass


def user_class(request, classid):
    try:
        # 获取课程对象
        course = Class.objects.get(classid=classid)

        # 处理课程详情页面渲染
        return render(request, 'course_detail.html', {'course': course})

    except Class.DoesNotExist:
        # 如果课程不存在，返回错误页面或其他处理方式
        return render(request, 'error.html', {'error': '课程未找到！'})


@csrf_exempt
@login_required
def add_course_ajax(request):
    if request.method == "POST":
        user = request.user

        # 验证用户是否为教师
        try:
            user_capacity = USER_TO_CAPACITY.objects.get(username=user).capacity
            if user_capacity != 2:
                return JsonResponse({'error': "您无权添加课程。"}, status=403)
        except USER_TO_CAPACITY.DoesNotExist:
            return JsonResponse({'error': "用户未绑定身份。"}, status=400)

        # 创建新课程
        classid = request.POST.get('classid')
        classname = request.POST.get('classname', "Unknown Class")

        # 验证课程ID唯一性
        if Class.objects.filter(classid=classid).exists():
            return JsonResponse({'error': "课程ID已存在。"}, status=400)

        # 创建课程
        new_course = Class.objects.create(classid=classid, classname=classname, teacher=user)
        new_course.save()
        return JsonResponse({'message': "课程添加成功！"})

    return JsonResponse({'error': "无效的请求方法。"}, status=405)


@login_required
def course_detail(request, classid):
    course = get_object_or_404(Class, classid=classid)
    msgs = EMOJI_MESSAGE.objects.filter(classid=course).order_by('-time')  # 获取该课程的所有消息
    emojis = EMOJI.objects.all()  # 获取所有 emoji

    return render(request, 'course_detail.html', {'course': course, 'messages': msgs, 'emojis': emojis})


@login_required
def send_message_ajax(request, classid):
    if request.method == "POST":
        try:
            # 获取当前课程对象
            course = Class.objects.get(classid=classid)

            # 获取发送消息的用户
            user = request.user

            # 获取用户传来的 emoji_id
            emoji_id = request.POST.get('emoji_id')

            # 如果没有提供 emoji_id，则返回错误
            if not emoji_id:
                return JsonResponse({'error': '请提供有效的 Emoji ID！'}, status=400)

            # 查找 emoji 对象
            try:
                emoji = EMOJI.objects.get(id=emoji_id)
            except EMOJI.DoesNotExist:
                return JsonResponse({'error': '无效的 Emoji ID！'}, status=400)

            # 保存 emoji 消息记录
            EMOJI_MESSAGE.objects.create(
                sender=user,
                emoji_id=emoji,
                classid=course
            )

            # 返回成功响应
            return JsonResponse({'message': 'Emoji 消息已发送！'}, status=200)

        except Class.DoesNotExist:
            return JsonResponse({'error': '课程不存在！'}, status=404)

    # 如果请求方法不是 POST，返回 405 错误
    return JsonResponse({'error': '无效的请求方式！'}, status=405)


def send_emoji(request):  ##学生点击发送表情后触发
    pass


def emoji_history(request):  ##学生点击查询课程历史表情后触发
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
