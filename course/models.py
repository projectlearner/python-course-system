from django.db import models
from django.contrib.auth.models import User  # 引用內建使用者
from django.core.exceptions import ValidationError #避免重複
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="分類名稱")
    
    def __str__(self):
        return self.name
    
class CourseTime(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="times")
    weekday = models.IntegerField(choices=[(i, F"週{i}") for i in range(1,8)], verbose_name="星期幾")
    period = models.IntegerField(verbose_name="第幾節")

    def clean(self):
        super().clean()
        
        # 1. 確保該 Course 有設定教室
        if not hasattr(self, 'course') or not self.course or not self.course.classroom:
            return

        # 2. 搜尋是否有「同一天、同一節、同教室」的競爭課程
        conflict = CourseTime.objects.filter(
            weekday=self.weekday,
            period=self.period,
            course__classroom=self.course.classroom
        ).exclude(pk=self.pk) # 排除自己（編輯時使用）

        if conflict.exists():
            conflicting_course = conflict.first().course
            raise ValidationError(
                f"教室衝堂！【{self.course.get_classroom_display()}】在 週{self.weekday} 第{self.period}節 "
                f"已經被課程「{conflicting_course.title}」佔用。"
            )

    def save(self, *args, **kwargs):
        # 儲存前強制觸發 clean() 驗證
        self.full_clean()
        super().save(*args, **kwargs)

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

# courses/models.py (或 course/models.py)
class Course(models.Model):
    CLASSROOM_CHOICES = [
        ('IM_LAB', '資管系電腦教室 (B501)'),
        ('BA_ROOM', '財稅系專業教室 (A302)'),
        ('FIN_ROOM', '財金系金融實驗室 (C401)'),
        ('ACC_ROOM', '會資系電腦教室 (A201)'),
        ('IB_ROOM', '國貿系多媒體教室 (B302)'),
        ('AM_ROOM', '企管系專業教室 (C205)'),
    ]

    title = models.CharField(max_length=100, verbose_name="課程名稱")
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name="分類")
    teacher = models.ForeignKey('users.TeacherProfile', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="授課教師")
    description = models.TextField(verbose_name="課程描述", blank=True)
    capacity = models.IntegerField(default=50, verbose_name="名額限制")
    
    # 新增教室欄位
    classroom = models.CharField(
        max_length=20, 
        choices=CLASSROOM_CHOICES, 
        default='IM_LAB', 
        verbose_name="上課教室"
    )

    def __str__(self):
        return self.title
