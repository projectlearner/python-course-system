from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

DEPARTMENT_CHOICES = [
    ('IM', '資訊管理系'),
    ('FIN', '財務金融系'),
    ('BA', '企業管理系'),
    ('PF', '財政稅務系'),
    ('ACCT', '會計資訊系'),
    ('IB', '國際貿易系'),
    ('GEN', '通識教育中心'),
]

CATEGORY_CHOICES = [
    ('REQUIRED', '專業必修'),
    ('ELECTIVE', '專業選修'),
    ('GENERAL', '通識課程'),
]


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="分類名稱")

    def __str__(self):
        return self.name


class CourseTime(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="times")
    weekday = models.IntegerField(choices=[(i, f"週{i}") for i in range(1, 8)], verbose_name="星期幾")
    period = models.IntegerField(verbose_name="第幾節")

    def clean(self):
        super().clean()

        # 如果尚未關聯課程，直接跳過驗證
        if not hasattr(self, 'course') or not self.course:
            return

        # 1. 教室衝堂檢查 (同星期、同節次、同教室)
        if self.course.classroom:
            classroom_conflict = CourseTime.objects.filter(
                weekday=self.weekday,
                period=self.period,
                course__classroom=self.course.classroom
            )
            # 只有當 course 已儲存時才需要 exclude(course=self.course)
            if self.course.pk:
                classroom_conflict = classroom_conflict.exclude(course=self.course)

            if classroom_conflict.exists():
                conflicting_course = classroom_conflict.first().course
                raise ValidationError(
                    f"教室衝堂！【{self.course.get_classroom_display()}】在 週{self.weekday} 第{self.period}節 "
                    f"已經被課程「{conflicting_course.title}」佔用。"
                )

        # 2. 教師時間衝堂檢查 (同星期、同節次、同教師)
        if self.course.teacher:
            teacher_conflict = CourseTime.objects.filter(
                weekday=self.weekday,
                period=self.period,
                course__teacher=self.course.teacher
            )
            # 只有當 course 已儲存時才需要 exclude(course=self.course)
            if self.course.pk:
                teacher_conflict = teacher_conflict.exclude(course=self.course)

            if teacher_conflict.exists():
                conflicting_course = teacher_conflict.first().course
                teacher_name = self.course.teacher.user.get_full_name() or self.course.teacher.user.username
                raise ValidationError(
                    f"教師排課衝堂！{teacher_name} 老師在 週{self.weekday} 第{self.period}節 "
                    f"已有授課項目「{conflicting_course.title}」。"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.title} - 週{self.weekday} 第{self.period}節"

class Enrollment(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(
        'users.StudentProfile',
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="選課時間")

    daily_score = models.FloatField(null=True, blank=True, verbose_name="平時成績")
    midterm_score = models.FloatField(null=True, blank=True, verbose_name="期中成績")
    final_score = models.FloatField(null=True, blank=True, verbose_name="期末成績")

    class Meta:
        unique_together = ("student", "course")

    @property
    def final_grade(self):
        """根據課程動態設定的配分比例計算總成績"""
        if self.daily_score is None or self.midterm_score is None or self.final_score is None:
            return None

        total = (
            self.daily_score * (self.course.daily_weight / 100.0) +
            self.midterm_score * (self.course.midterm_weight / 100.0) +
            self.final_score * (self.course.final_weight / 100.0)
        )
        return round(total, 1)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title}"


class Course(models.Model):
    CLASSROOM_CHOICES = [
        ('IM_LAB', '電606(承曦樓)'),
        ('BA_ROOM', '藝305'),
        ('FIN_ROOM', '撞球教室'),
        ('ACC_ROOM', '藝409'),
        ('IB_ROOM', '資401'),
        ('AM_ROOM', '電708(承曦樓)'),
        ('EN_ROOM', '承405'),
        ('CH_ROOM', '藝303'),
    ]

    title = models.CharField(max_length=100, verbose_name="課程名稱")
    teacher = models.ForeignKey('users.TeacherProfile', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="授課教師")
    classroom = models.CharField(max_length=20, choices=CLASSROOM_CHOICES, default='IM_LAB', verbose_name="上課教室")
    description = models.TextField(blank=True, verbose_name="課程大綱")
    capacity = models.PositiveIntegerField(default=60, verbose_name="名額上限")
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES, default='IM', verbose_name="開課系所")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='REQUIRED', verbose_name="課程類別")
    credits = models.PositiveIntegerField(default=3, verbose_name="學分數")

    # 動態成績比例欄位
    daily_weight = models.IntegerField(
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="平時成績佔比(%)"
    )
    midterm_weight = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="期中成績佔比(%)"
    )
    final_weight = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="期末成績佔比(%)"
    )

    def clean(self):
        super().clean()

        # 1. 驗證配分加總必須為 100%
        total_weight = self.daily_weight + self.midterm_weight + self.final_weight
        if total_weight != 100:
            raise ValidationError(f"成績比例加總必須等於 100%！（目前加總為：{total_weight}%）")

        # 2. 修改教室或變更教師時，重新檢查該課程所有既存時段是否會引發衝堂
        if self.pk:
            for course_time in self.times.all():
                # 檢查教室衝突
                classroom_conflict = CourseTime.objects.filter(
                    weekday=course_time.weekday,
                    period=course_time.period,
                    course__classroom=self.classroom
                ).exclude(course=self).exists()

                if classroom_conflict:
                    raise ValidationError(
                        f"變更教室失敗！【{self.get_classroom_display()}】在 週{course_time.weekday} 第{course_time.period}節 已被其他課程佔用。"
                    )

                # 檢查教師衝突
                if self.teacher:
                    teacher_conflict = CourseTime.objects.filter(
                        weekday=course_time.weekday,
                        period=course_time.period,
                        course__teacher=self.teacher
                    ).exclude(course=self).exists()

                    if teacher_conflict:
                        raise ValidationError(
                            f"無法變更！授課教師在 週{course_time.weekday} 第{course_time.period}節 已有其他授課項目。"
                        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title