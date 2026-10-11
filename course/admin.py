from django.contrib import admin
from .models import Category, Course, CourseTime, Enrollment
from .models import SystemSetting    
# Register your models here.
admin.site.register(Category)
admin.site.register(CourseTime)
admin.site.register(Enrollment)

class CourseTimeInline(admin.TabularInline):
    model = CourseTime
    extra = 3  # 預設直接開 3 列輸入框，方便一次填完如第 2、3、4 節

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')
    inlines = [CourseTimeInline]  # 將時段嵌入課程編輯頁面

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('current_phase',)