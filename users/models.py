from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

DEPARTMENT_CHOICES = [
    ('IM', '資訊管理系'),
    ('FIN', '財務金融系'),
    ('BA', '企業管理系'),
    ('PF', '財政稅務系'),
    ('ACCT', '會計資訊系'),
    ('IB', '國際貿易系'),
    ('GEN', '通識教育中心'),
]


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True, verbose_name="學號")
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES, verbose_name="系所")

    GRADE_CHOICES = [
        (1, '大一'),
        (2, '大二'),
        (3, '大三'),
        (4, '大四'),
    ]
    grade = models.IntegerField(choices=GRADE_CHOICES, default=2, verbose_name="年級")
    max_credits = models.IntegerField(default=25, verbose_name="單學期學分上限")

    def save(self, *args, **kwargs):
        # 自動保持 User 的 username 與學號同步
        if self.user and self.student_id and self.user.username != self.student_id:
            self.user.username = self.student_id
            self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
        full_name = f"{self.user.last_name}{self.user.first_name}".strip()
        display_name = full_name if full_name else self.user.username
        return f"{self.student_id} - {display_name}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=20, unique=True, verbose_name="教職員代號")
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES, verbose_name="系所")

    def save(self, *args, **kwargs):
        # 自動保持 User 的 username 與教職員代號同步
        if self.user and self.teacher_id and self.user.username != self.teacher_id:
            self.user.username = self.teacher_id
            self.user.save()
        super().save(*args, **kwargs)

    @property
    def name(self):
        full_name = f"{self.user.last_name}{self.user.first_name}".strip()
        return full_name if full_name else self.user.username

    def __str__(self):
        return f"{self.teacher_id} - {self.name} 老師"