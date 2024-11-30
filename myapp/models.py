from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# username与身份的对应关系表
class USER_TO_CAPACITY(models.Model):
    CAPACITY_CHOICES = [
        (1, '学生'),
        (2, '教师'),
        (3, '管理员')
    ]

    username = models.OneToOneField(User, on_delete=models.CASCADE)
    capacity = models.IntegerField(choices=CAPACITY_CHOICES)


class Class(models.Model):
    classid = models.CharField(max_length=20, unique=True)  # 课程唯一标识，必填
    classname = models.CharField(max_length=100,
                                 default="Unknown Class", null=True, blank=True)  # 课程名称，可为空，带默认值
    teacher = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='teacher_classes', null=True, blank=True)  # 授课教师，可为空
    students = models.ManyToManyField(User, related_name='student_classes', blank=True)  # 学生名单，可为空
    #注:manytomanyfield实际上是创建了另一个classid和student的对应表

    def __str__(self):
        return self.classname or "Unknown Class"  # 如果 classname 为空，显示 "Unknown Class"


def validate_emoji_id(value):
    if value < 0 or value > 64:
        raise ValidationError('emoji_id must be between 0 and 64.')


class EMOJI_MESSAGE(models.Model):
    # 发送消息的用户，关联 User 模型
    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    # 使用的 emoji，关联 EMOJI 模型
    emoji_id = models.ForeignKey('EMOJI', on_delete=models.CASCADE)

    # 消息发送时间
    time = models.DateTimeField(auto_now_add=True)

    # 消息所属课程，关联 Class 模型
    classid = models.ForeignKey('Class', on_delete=models.CASCADE)



class EMOJI(models.Model):
    id = models.AutoField(primary_key=True)  # 递增的计数器
    U_code = models.CharField(max_length=10, unique=True)