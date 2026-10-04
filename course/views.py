# courses/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Course, Enrollment, CourseTime, DEPARTMENT_CHOICES, CATEGORY_CHOICES
from django.views.decorators.http import require_POST


def course_list(request):
    selected_dept = request.GET.get('dept', '') # 取得前端傳來的系所篩選條件
    
    # 使用 select_related 避免外鍵查詢的 N+1 問題
    courses = Course.objects.select_related('teacher').all()

    # 1. 根據下拉選單篩選系所
    if selected_dept:
        courses = courses.filter(department=selected_dept)

    # 2. 取得目前登入學生的 Profile
    student_profile = getattr(request.user, 'student_profile', None)

    # 3. 為每門課程標記是否與學生同系所，並建立簡易可選狀態
    course_data = []
    for course in courses:
        # 基本邏輯：若是通識 OR 與學生同系所 -> 可選；否則 -> 提示外系課程
        is_same_dept = student_profile and (course.department == student_profile.department)
        is_general = (course.category == 'GENERAL')
        
        # 目前階段預設：可選 (同系或通識)
        can_enroll = is_same_dept or is_general

        course_data.append({
            'course': course,
            'is_same_dept': is_same_dept,
            'can_enroll': can_enroll,
        })

    context = {
        'course_data': course_data,  # 📍 修正：必須傳遞包裝後的 course_data 給前端模板
        'department_choices': DEPARTMENT_CHOICES,
        'selected_dept': selected_dept,
    }
    return render(request, 'courses/course_list.html', context)

def course_detail(request, course_id):
    """課程詳情"""
    # 加上 prefetch_related('times')，一次性拿好時間資料
    course = get_object_or_404(Course.objects.prefetch_related('times'), id=course_id)
    
    is_enrolled = False
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        is_enrolled = Enrollment.objects.filter(
            student=request.user.student_profile, 
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
        
        # 1. 驗證學生身份
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, '只有學生身份可以進行選課！')
            return redirect('courses:course_detail', course_id=course.id)
            
        student = request.user.student_profile

        # 2. 檢查是否重複選課
        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.warning(request, '你已經選過這門課程了。')
            return redirect('courses:course_detail', course_id=course.id)

        # 3. 檢查學生課表是否衝堂 (先拿已選課程 ID，再查時間)
        enrolled_course_ids = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
        student_enrolled_times = set(
            CourseTime.objects.filter(course_id__in=enrolled_course_ids).values_list('weekday', 'period')
        )
        new_course_times = set(
            course.times.values_list('weekday', 'period')
        )

        overlapping_times = student_enrolled_times.intersection(new_course_times)
        if overlapping_times:
            conflict_msg = ", ".join([f"週{w}第{p}節" for w, p in sorted(overlapping_times)])
            messages.error(request, f'選課失敗：與已選課程時間衝堂（{conflict_msg}）！')
            return redirect('courses:course_detail', course_id=course.id)

        # 4. 檢查名額限制與原子性操作
        with transaction.atomic():
            course_obj = Course.objects.select_for_update().get(id=course_id)
            current_enrolled = Enrollment.objects.filter(course=course_obj).count()
            
            if hasattr(course_obj, 'capacity') and current_enrolled >= course_obj.capacity:
                messages.error(request, '選課失敗：該課程名額已滿！')
                return redirect('courses:course_detail', course_id=course.id)

            # 5. 建立選課紀錄
            Enrollment.objects.create(student=student, course=course_obj)
            messages.success(request, f'成功加選課程：{course_obj.title}！')

        return redirect('courses:my_courses')

    return redirect('courses:course_list')

# courses/views.py

@login_required
def my_courses(request):
    """個人課表/已選課程列表"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, '請先完善學生資料。')
        return redirect('courses:course_list')
        
    student = request.user.student_profile
    enrollments = Enrollment.objects.filter(student=student).select_related('course').prefetch_related('course__times')

    # 初始化 5x8 的課表矩陣: { weekday: { period: [course_times] } }
    timetable_matrix = {day: {period: [] for period in range(1, 9)} for day in range(1, 6)}

    for enrollment in enrollments:
        for time_slot in enrollment.course.times.all():
            if 1 <= time_slot.weekday <= 5 and 1 <= time_slot.period <= 8:
                timetable_matrix[time_slot.weekday][time_slot.period].append(time_slot)

    # 節次與對應時間對照表
    PERIOD_TIMES = {
        1: '08:10 - 09:00',
        2: '09:10 - 10:00',
        3: '10:10 - 11:00',
        4: '11:10 - 12:00',
        5: '13:10 - 14:00',
        6: '14:10 - 15:00',
        7: '15:10 - 16:00',
        8: '16:10 - 17:00',
    }

    grid = []
    for period in range(1, 9):
        row = []
        for day in range(1, 6):
            row.append(timetable_matrix[day][period])
        # 把時間直接包進 tuple 傳給 template
        grid.append((period, PERIOD_TIMES.get(period, ''), row))

    return render(request, 'courses/my_courses.html', {
        'enrollments': enrollments,
        'grid': grid,  # 傳送處理好的二維列表給 template
    })

@login_required
def drop_course(request, course_id):
    """退選課程邏輯"""
    if request.method == 'POST':
        # 1. 驗證學生身份
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, '只有學生身份可以進行退選！')
            return redirect('courses:my_courses')

        student = request.user.student_profile
        course = get_object_or_404(Course, id=course_id)

        # 2. 尋找並刪除選課紀錄
        enrollment = Enrollment.objects.filter(student=student, course=course).first()
        if enrollment:
            enrollment.delete()
            messages.success(request, f'已成功退選課程：{course.title}！')
        else:
            messages.error(request, '退選失敗：你尚未選修此門課程。')

        return redirect('courses:my_courses')

    return redirect('courses:my_courses')