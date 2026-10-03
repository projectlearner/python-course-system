# courses/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Course, Enrollment

def course_list(request):
    """課程列表"""
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

def course_detail(request, course_id):
    """課程詳情"""
    course = get_object_or_404(Course, id=course_id)
    # 檢查當前登入學生是否已加選
    is_enrolled = False
    if request.user.is_authenticated and hasattr(request.user, 'studentprofile'):
        is_enrolled = Enrollment.objects.filter(
            student=request.user.studentprofile, 
            course=course
        ).exists()
        
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'is_enrolled': is_enrolled
    })

@login_required
def enroll_course(request, course_id):
    """加選課程邏輯"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        
        # 1. 驗證是否為學生身份
        if not hasattr(request.user, 'studentprofile'):
            messages.error(request, '只有學生身份可以進行選課！')
            return redirect('courses:course_detail', course_id=course.id)
            
        student = request.user.studentprofile

        # 2. 檢查是否重複選課
        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.warning(request, '你已經選過這門課程了。')
            return redirect('courses:course_detail', course_id=course.id)

        # 3. 檢查名額限制與原子性操作（避免高併發搶課漏洞）
        with transaction.atomic():
            # 鎖定該筆課程資料確保人數計算準確
            course_obj = Course.objects.select_for_update().get(id=course_id)
            current_enrolled = Enrollment.objects.filter(course=course_obj).count()
            
            if hasattr(course_obj, 'capacity') and current_enrolled >= course_obj.capacity:
                messages.error(request, '選課失敗：該課程名額已滿！')
                return redirect('courses:course_detail', course_id=course.id)

            # 4. 建立選課紀錄
            Enrollment.objects.create(student=student, course=course_obj)
            messages.success(request, f'成功加選課程：{course_obj.title}！')

        return redirect('courses:my_courses')

    return redirect('courses:course_list')

@login_required
def my_courses(request):
    """個人課表/已選課程列表"""
    if not hasattr(request.user, 'studentprofile'):
        messages.error(request, '請先完善學生資料。')
        return redirect('courses:course_list')
        
    enrollments = Enrollment.objects.filter(student=request.user.studentprofile).select_related('course')
    return render(request, 'courses/my_courses.html', {'enrollments': enrollments})

# courses/views.py
@login_required
def drop_course(request, course_id):
    """退選課程邏輯"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        
        if not hasattr(request.user, 'studentprofile'):
            messages.error(request, '身分驗證失敗。')
            return redirect('courses:my_courses')

        student = request.user.studentprofile
        enrollment = Enrollment.objects.filter(student=student, course=course).first()

        if enrollment:
            enrollment.delete()
            messages.success(request, f'已成功退選課程：{course.title}')
        else:
            messages.warning(request, '您並未加選該門課程。')

    return redirect('courses:my_courses')