from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class TeacherProfile(models.Model):
    # 延伸 User (1:1) 載入django內建的使用者模型(專門管登入相關的,class內的其他內容他不管) 
    # 其餘寫在這個class內的都歸TeacherProfile管(如bio)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    bio = models.TextField(blank=True, verbose_name="教師簡介")

    def __str__(self):
        return f"教師: {self.user.username}"

class StudentProfile(models.Model):
    # 延伸 User (1:1)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True, verbose_name="學號")

    def __str__(self):
        return f"學生: {self.user.username} ({self.student_id})"