# Generated by Django 5.1.1 on 2024-11-28 02:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="class",
            name="classname",
            field=models.CharField(
                blank=True, default="Unknown Class", max_length=100, null=True
            ),
        ),
        migrations.AddField(
            model_name="class",
            name="teacher",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="teacher_classes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="class",
            name="students",
            field=models.ManyToManyField(
                blank=True, related_name="student_classes", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.DeleteModel(
            name="TEACHER_TO_CLASS",
        ),
    ]
