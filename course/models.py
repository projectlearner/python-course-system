from django.db import models
from django.contrib.auth.models import User  # 引用內建使用者
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="分類名稱")
    
    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=100, verbose_name="課程名稱")

    description = models.TextField(blank=True, verbose_name="課程大綱")

    credits = models.IntegerField(default=3, verbose_name="學分")

    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name="course"
    )

    teacher = models.ForeignKey(
        'users.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="course"
    )

    def __str__(self):
        return self.title

class CourseTime(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="times")

    weekday = models.IntegerField(choices=[(i, F"週{i}") for i in range(1,8)], verbose_name="星期幾")
    period = models.IntegerField(verbose_name="第幾節")

    def __str__(self):
        return f"{self.course.title} - 週{self.weekday} 第{self.period}節"

class Enrollment(models.Model):
    course = models.ForeignKey('Course',on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(
        'users.StudentProfile',
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="選課時間")
    grade = models.FloatField(null=True, blank=True, verbose_name="成績")

    class Meta:
        unique_together = ("student", "course")
        #約束學生和課程的組合不會重複eg.小明+微積分和小明+程式設計可以存在 但如果已經選小明+程式語言的情況下再選一次小明+程式語言則會擋下來


    def __str__(self):
        return f"{self.student.user.username} - {self.course.title}"
    