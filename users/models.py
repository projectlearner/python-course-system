from django.db import models
from django.contrib.auth.models import User

# Create your models here.

DEPARTMENT_CHOICES = [
    ('IM', '資訊管理系'),
    ('FIN', '財務金融系'),
    ('BA', '企業管理系'),
    ('PF', '財政稅務系'),
    ('ACCT', '會計資訊系'),
    ('IB', '國際貿易系'),
]

class TeacherProfile(models.Model):
    # 延伸 User (1:1) 載入django內建的使用者模型(專門管登入相關的,class內的其他內容他不管) 
    # 其餘寫在這個class內的都歸TeacherProfile管(如bio)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    name = models.CharField(max_length=50)
    bio = models.TextField(blank=True, verbose_name="教師簡介")

    def __str__(self):
        return self.name

class StudentProfile(models.Model):
    # 延伸 User (1:1)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True, verbose_name="學號")
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES, default='IM', verbose_name="所屬系所")

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name() or self.user.username}"