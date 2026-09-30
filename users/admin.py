from django.contrib import admin
from .models import TeacherProfile, StudentProfile

# Register your models here.
admin.site.register(TeacherProfile)
admin.site.register(StudentProfile)