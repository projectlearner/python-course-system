from django.contrib import admin
from .models import TeacherProfile, StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name', 'department', 'grade')
    search_fields = ('student_id', 'user__last_name', 'user__first_name', 'user__username')
    list_filter = ('department', 'grade')

    @admin.display(description='姓名')
    def get_full_name(self, obj):
        name = f"{obj.user.last_name}{obj.user.first_name}".strip()
        return name if name else obj.user.username


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'name', 'department')
    search_fields = ('teacher_id', 'user__last_name', 'user__first_name', 'user__username')
    list_filter = ('department',)