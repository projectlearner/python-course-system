from django.contrib import admin
from .models import Category, Course, CourseTime, Enrollment

# Register your models here.
admin.site.register(Category)
admin.site.register(Course)
admin.site.register(CourseTime)
admin.site.register(Enrollment)