from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import auth, messages
from myapp.models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
import json,os
from django.shortcuts import render, HttpResponseRedirect,get_object_or_404
from django.db.models import Count
from django.core.paginator import Paginator
from django.conf import settings
from django.db import transaction


def user_login(request):
    return redirect('login')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)

        if user:
            auth.login(request, user)  # 这里做了登录
            return redirect('home')  # 登录成功后重定向到主页
        else:
            messages.error(request, '账号或密码错误')
            return render(request, "login.html", {'username': username})

    # 在 GET 请求时，防止浏览器缓存页面
    response = render(request, "login.html")
    response['Cache-Control'] = 'no-store'  # 禁止浏览器缓存
    return response


def register(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            name = request.POST.get('real_name', None)  # 获取真实姓名
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
            USER_TO_CAPACITY.objects.create(username=user,name=name, capacity=capacity)
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
    # 检查用户权限
    user = request.user
    try:
        user_capacity = USER_TO_CAPACITY.objects.get(username=user).capacity
    except USER_TO_CAPACITY.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': "用户未绑定身份。"})

    if user_capacity != 3:
        return render(request, 'error_page.html', {'error_message': "无权限访问该页面。"})

    # 查询课程和学生统计信息
    all_classes = Class.objects.all()
    class_stats = [
        {
            'class': cls,
            'classid': cls.classid,
            'student_count': cls.students.count(),
            'message_count': EMOJI_MESSAGE.objects.filter(classid=cls).count(),  # 获取消息数
            'teacher_name': USER_TO_CAPACITY.objects.filter(
                username=cls.teacher).first().name if cls.teacher else "未设置教师姓名",
        }
        for cls in all_classes
    ]

    # 分页处理课程信息
    paginator_classes = Paginator(class_stats, 10)  # 每页10条
    page_number_classes = request.GET.get('class_page', 1)
    page_obj_classes = paginator_classes.get_page(page_number_classes)

    # 用户统计信息
    total_users = User.objects.count()
    users_sorted_by_login = User.objects.order_by('-last_login')
    user_stats = [
        {
            'user': user,
            'capacity': USER_TO_CAPACITY.objects.get(username=user).capacity,
            'name': USER_TO_CAPACITY.objects.filter(username=user).first().name or "*未设置姓名*",
        }
        for user in users_sorted_by_login
    ]
    paginator_users = Paginator(user_stats, 10)  # 每页10条
    page_number_users = request.GET.get('user_page', 1)
    page_obj_users = paginator_users.get_page(page_number_users)

    # 获取表情信息
    total_emoji = EMOJI.objects.count()
    emoji_list = EMOJI.objects.all()
    paginator_emoji = Paginator(emoji_list, 10)  # 每页显示10个表情

    emoji_page_number = request.GET.get('emoji_page', 1)  # 获取 emoji 当前页
    page_obj_emoji = paginator_emoji.get_page(emoji_page_number)
    # 渲染模板
    return render(request, 'admin_home.html', {
        'page_obj_classes': page_obj_classes,  # 课程分页对象
        'total_classes': all_classes.count(),
        'page_obj_users': page_obj_users,      # 用户分页对象
        'total_users': total_users,
        'page_obj_emoji': page_obj_emoji,      # 表情分页对象
        'total_emoji':total_emoji,
    })


def manage_emoji(request):
    if request.method == "POST":
        U_code = request.POST.get("emojiCode").strip()
        description = request.POST.get("emojiDesc").strip()

        # 确保图片文件存在
        static_root = settings.STATIC_ROOT or settings.STATICFILES_DIRS[0]  # 兼容开发环境
        image_path = os.path.join(static_root, f"emoji/{U_code}.png")
        if not os.path.exists(image_path):
            return JsonResponse({"success": False, "message": "对应的图片文件不存在，请确保文件已上传。"})

        # 创建或更新 Emoji 对象
        emoji, created = EMOJI.objects.get_or_create(U_code=U_code)
        emoji.description = description
        emoji.save()

        return JsonResponse({
            "success": True,
            "message": "Emoji 已成功保存。",
            "created": created  # True 如果新建，False 如果更新
        })

    return JsonResponse({"success": False, "message": "仅支持 POST 请求。"})


def remove_emoji(request):
    """API endpoint to remove an emoji."""
    if request.method == "POST":
        try:
            # Parse the incoming JSON payload
            data = json.loads(request.body)
            emoji_id = data.get("emojiId")

            if not emoji_id:
                return JsonResponse({"success": False, "message": "未提供有效的 Emoji ID。"})

            # Locate the emoji record
            emoji = EMOJI.objects.get(id=emoji_id)

            # Remove the database entry
            emoji.delete()

            return JsonResponse({"success": True, "message": "Emoji 已成功移除。"})

        except EMOJI.DoesNotExist:
            return JsonResponse({"success": False, "message": "指定的 Emoji 不存在。"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"移除过程中出现错误: {str(e)}"})

    return JsonResponse({"success": False, "message": "仅支持 POST 请求。"})


def error_page(request):
    return render(request, 'error_page.html')


@csrf_exempt
@login_required
def add_course_ajax(request):
    if request.method == "POST":
        user = request.user

        # 验证用户是否为教师
        try:
            user_capacity = USER_TO_CAPACITY.objects.get(username=user).capacity
            if user_capacity != 2:
                return JsonResponse({'success': False, 'error': "您无权添加课程。"}, status=403)
        except USER_TO_CAPACITY.DoesNotExist:
            return JsonResponse({'success': False, 'error': "用户未绑定身份。"}, status=400)

        # 创建新课程
        classid = request.POST.get('classid')
        classname = request.POST.get('classname', "Unknown Class")

        # 验证课程ID唯一性
        if Class.objects.filter(classid=classid).exists():
            return JsonResponse({'success': False, 'error': "课程ID已存在。"}, status=400)

        # 创建课程
        new_course = Class.objects.create(classid=classid, classname=classname, teacher=user)
        new_course.save()

        return JsonResponse({'success': True, 'message': "课程添加成功！"})

    return JsonResponse({'success': False, 'error': "无效的请求方法。"}, status=405)


@login_required
def course_detail(request, classid):
    try:
        # 获取课程信息
        course = Class.objects.get(classid=classid)
        total_students = course.students.count()  # 获取学生人数
        emojis = EMOJI.objects.all()  # 获取所有表情
        msgs = EMOJI_MESSAGE.objects.filter(classid=course)  # 获取该课程的消息

        try:
            teacher_capacity = USER_TO_CAPACITY.objects.get(username=course.teacher)
            teacher_name = teacher_capacity.name if teacher_capacity.name else "未提供姓名"
        except USER_TO_CAPACITY.DoesNotExist:
            teacher_name = "未找到教师信息"
        # 统计表情消息
        total_emoji_count = msgs.exclude(emoji_id__isnull=True).count()  # 总发送表情数
        top_5_emojis = (
            msgs.values('emoji_id__description', 'emoji_id__U_code')  # 使用有效字段
            .annotate(count=Count('emoji_id'))
            .order_by('-count')[:5]
        )

        # 将统计数据封装到字典中
        emoji_statistics = {
            'total_count': total_emoji_count,
            'top_emojis': top_5_emojis,
        }

        # 获取当前用户的角色
        user_capacity = USER_TO_CAPACITY.objects.get(username=request.user).capacity

        # 判断当前用户是否是教师
        is_teacher = user_capacity == 2  # 如果是教师，capacity 值为 2

        return render(request, 'course_detail.html', {
            'course': course,
            'teacher_name':teacher_name,
            'total_students': total_students,
            'emojis': emojis,
            'messages': msgs,
            'emoji_statistics': emoji_statistics,  # 传递表情统计数据
            'is_teacher': is_teacher,  # 传递用户是否为教师的信息
        })
    except Class.DoesNotExist:
        # 如果课程不存在，返回上一页面（原页面）
        referer = request.META.get('HTTP_REFERER', '/')  # 获取来源页面，如果没有则跳转到主页
        return HttpResponseRedirect(referer)  # 返回上一页，或指定一个主页 URL


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


@login_required
def admin_class_detail(request, classid):
    # 检查用户权限
    user = request.user
    try:
        user_capacity = USER_TO_CAPACITY.objects.get(username=user).capacity
    except USER_TO_CAPACITY.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': "用户未绑定身份。"})

    if user_capacity != 3:  # 3 表示管理员权限
        return render(request, 'error_page.html', {'error_message': "无权限访问该页面。"})

    # 获取课程信息
    try:
        course = Class.objects.get(classid=classid)
    except Class.DoesNotExist:
        return JsonResponse({"message": "课程不存在"}, status=404)

    try:
        teacher_capacity = USER_TO_CAPACITY.objects.get(username=course.teacher)
        teacher_name = teacher_capacity.name if teacher_capacity.name else "未提供姓名"
    except USER_TO_CAPACITY.DoesNotExist:
        teacher_name = "未找到教师信息"

    students = course.students.all()
    student_info = []
    for student in students:
        try:
            user_to_capacity = USER_TO_CAPACITY.objects.get(username=student)
            student_name = user_to_capacity.name  # 从 USER_TO_CAPACITY 获取学生姓名
        except USER_TO_CAPACITY.DoesNotExist:
            student_name = "未设置姓名"  # 若未绑定扩展信息，设置默认值
        student_info.append({
            'id':student.id,
            'name': student_name,
            'username': student.username,
            'email': student.email,
        })
    # 统计学生数量
    total_students = course.students.count()

    # 获取过往消息
    messages = EMOJI_MESSAGE.objects.filter(classid=course).select_related('sender', 'emoji_id')

    # 表情统计
    emoji_statistics = EMOJI_MESSAGE.objects.filter(classid=course).values(
        'emoji_id__U_code', 'emoji_id__description'
    ).annotate(count=Count('emoji_id')).order_by('-count')[:5]

    # 总表情数
    total_emoji_count = EMOJI_MESSAGE.objects.filter(classid=course).count()

    context = {
        'course': course,
        'teacher_name': teacher_name,
        'student_info': student_info,
        'total_students': total_students,
        'messages': messages,
        'emoji_statistics': {
            'total_count': total_emoji_count,
            'top_emojis': emoji_statistics,
        },
    }
    return render(request, 'admin_class_detail.html', context)


@login_required
def edit_teacher(request, classid):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            teacher_username = data.get("teacher_username")

            if not teacher_username:
                return JsonResponse({"error": "教师用户名不能为空"}, status=400)

            new_teacher = User.objects.get(username=teacher_username)
            course = Class.objects.get(classid=classid)

            course.teacher = new_teacher
            course.save()

            return JsonResponse({"success": True})
        except User.DoesNotExist:
            return JsonResponse({"error": "教师用户不存在"}, status=404)
        except Class.DoesNotExist:
            return JsonResponse({"error": "课程不存在"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "无效的请求方法"}, status=405)


@csrf_exempt
@login_required
def add_student(request):
    if not hasattr(request.user, 'user_to_capacity') or request.user.user_to_capacity.capacity != 2:
        # 检查是否为教师身份
        return JsonResponse({'success': False, 'error': '您无权限执行此操作。'})

    if request.method == 'POST':
        classid = request.POST.get('classid')
        student_username = request.POST.get('studentid')

        try:
            # 获取课程
            cls = Class.objects.get(classid=classid)

            # 检查是否为当前教师的课程
            if cls.teacher != request.user:
                return JsonResponse({'success': False, 'error': '您只能为自己的课程添加学生！'})

            # 获取学生
            student = User.objects.get(username=student_username)

            # 检查学生身份
            if not hasattr(student, 'user_to_capacity') or student.user_to_capacity.capacity != 1:
                return JsonResponse({'success': False, 'error': f'用户 {student_username} 不是学生身份，无法添加！'})

            # 检查学生是否已经在课程中
            if cls.students.filter(id=student.id).exists():
                return JsonResponse({'success': False, 'error': f'学生 {student_username} 已经在课程中！'})

            # 添加学生
            cls.students.add(student)
            return JsonResponse({'success': True})

        except ObjectDoesNotExist:
            return JsonResponse({'success': False, 'error': '课程或用户不存在！'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '无效请求！'})


@login_required
@require_GET
def get_students_in_course(request):
    classid = request.GET.get('classid')
    if not classid:
        return JsonResponse({'error': '课程ID缺失'}, status=400)

    try:
        course = Class.objects.get(classid=classid)
        students = course.students.all()

        # 获取学生的名称，假设学生是通过 USER_TO_CAPACITY 表与 User 模型关联的
        student_list = []
        for student in students:
            # 获取该学生在 USER_TO_CAPACITY 表中的对应记录
            user_capacity = USER_TO_CAPACITY.objects.get(username=student)
            student_list.append({
                'id': student.username,
                'name': user_capacity.name  # 从 USER_TO_CAPACITY 表中获取学生名称
            })

        return JsonResponse({'students': student_list}, status=200)

    except Class.DoesNotExist:
        return JsonResponse({'error': '课程不存在'}, status=404)
    except USER_TO_CAPACITY.DoesNotExist:
        return JsonResponse({'error': '用户身份未绑定'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def remove_student_from_course(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的 JSON 格式'}, status=400)

    classid = data.get('classid')
    studentid = data.get('studentid')
    print("OK")
    if not classid or not studentid:
        return JsonResponse({'error': '课程ID或学生ID缺失'}, status=400)

    try:
        course = Class.objects.get(classid=classid)
    except Class.DoesNotExist:
        return JsonResponse({'error': '课程不存在'}, status=404)

    try:
        student = User.objects.get(username=studentid)
    except User.DoesNotExist:
        return JsonResponse({'error': '学生不存在'}, status=404)

    try:
        course.students.remove(student)
        return JsonResponse({'success': True}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def remove_course(request, classid):
    # 确保请求方法为 POST
    if request.method == 'POST':
        # 获取课程对象
        course = get_object_or_404(Class, classid=classid)

        # 检查课程是否有学生或消息
        if course.students.exists() or EMOJI_MESSAGE.objects.filter(classid=course).exists():
            # 返回错误信息，不刷新页面
            return JsonResponse({'error': '无法移除课程，课程中有学生或消息。'}, status=400)

        # 如果没有学生和消息，删除课程
        course.delete()

        # 返回成功信息
        return JsonResponse({'success': True})

    return JsonResponse({'error': '无效的请求方法'}, status=405)


def delete_message(request, message_id):
    if request.method == "POST":
        # 获取要删除的消息
        message = get_object_or_404(EMOJI_MESSAGE, id=message_id)

        # 删除消息
        message.delete()

        # 返回 JSON 响应
        return JsonResponse({'success': True})

    # 如果请求方法不是 POST，返回失败
    return JsonResponse({'error': '请求方法错误'}, status=400)


@login_required
@require_POST
def add_user(request):
    try:
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        real_name = request.POST.get('real_name')  # 真实姓名
        capacity = request.POST.get('capacity')  # 身份: 1=学生, 2=教师, 3=管理员

        # 检查必填字段是否完整
        if not username or not email or not password or not real_name or not capacity:
            return JsonResponse({'success': False, 'error': '用户名、邮箱、密码、真实姓名和身份是必填项！'}, status=400)

        # 检查邮箱是否已被注册
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': '邮箱已被注册！'}, status=400)

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': '用户名已存在！'}, status=400)

        # 创建用户及其身份绑定
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            USER_TO_CAPACITY.objects.create(username=user, name=real_name, capacity=int(capacity))

        return JsonResponse({'success': True, 'message': '用户创建成功！'}, status=201)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def delete_user(request):
    try:
        user_id = request.POST.get('user_id')
        user_to_delete = get_object_or_404(User, id=user_id)

        # 检查用户是否为管理员
        try:
            user_capacity = USER_TO_CAPACITY.objects.get(username=user_to_delete)
            if user_capacity.capacity == 3:  # 管理员
                return JsonResponse({'success': False, 'error': '无法删除管理员用户！'}, status=403)
        except USER_TO_CAPACITY.DoesNotExist:
            return JsonResponse({'success': False, 'error': '用户身份信息未绑定！'}, status=400)

        # 删除用户及其关联数据
        with transaction.atomic():
            if user_capacity.capacity == 1:  # 学生
                # 删除学生加入的课程
                for course in user_to_delete.student_classes.all():
                    course.students.remove(user_to_delete)

            elif user_capacity.capacity == 2:  # 教师
                # 删除教师教授的课程及其相关消息
                for course in Class.objects.filter(teacher=user_to_delete):
                    EMOJI_MESSAGE.objects.filter(classid=course).delete()  # 删除课程相关消息
                    course.delete()  # 删除课程

            # 删除用户发送的消息
            EMOJI_MESSAGE.objects.filter(sender=user_to_delete).delete()

            # 删除用户的身份绑定和用户本身
            user_capacity.delete()
            user_to_delete.delete()

        return JsonResponse({'success': True, 'message': '用户删除成功！'}, status=200)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
